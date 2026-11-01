"""Checks on the data, the semantic model (TMDL) and the report (PBIR) definitions."""

import json
import re
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MODEL = ROOT / "BarakaFinance.SemanticModel" / "definition"
REPORT = ROOT / "BarakaFinance.Report" / "definition"
sys.path.insert(0, str(ROOT / "analysis"))
import checkpoints  # noqa: E402

RATES = {"None": 0.0, "Low": 0.03, "Medium": 0.07, "High": 0.15}


# --------------------------------------------------------------------------- data
@pytest.fixture(scope="module")
def data():
    return checkpoints.load()


def test_row_counts(data):
    assert len(data["sales"]) == 6264
    assert len(data["targets"]) == 180
    assert len(data["products"]) == 6
    assert len(data["markets"]) == 7


def test_money_columns_reconcile(data):
    s = data["sales"]
    assert (s["units_sold"] * s["sale_price_kes"] == s["gross_sales_kes"]).all()
    assert (s["gross_sales_kes"] - s["discounts_kes"] == s["sales_kes"]).all()
    assert (s["sales_kes"] - s["cogs_kes"] == s["profit_kes"]).all()
    expected = s["gross_sales_kes"] * s["discount_band"].map(RATES)
    assert (s["discounts_kes"] - expected).abs().max() <= 1


def test_keys_match_dimensions(data):
    s, t = data["sales"], data["targets"]
    assert set(s["product"]) <= set(data["products"]["product"])
    assert set(s["market"]) <= set(data["markets"]["market"])
    assert set(s["discount_band"]) == set(RATES)
    assert set(s["segment"]) == set(t["segment"])
    assert data["products"]["product"].is_unique and data["markets"]["market"].is_unique
    for frame in (s, t):
        assert frame["month"].dt.day.eq(1).all()
        assert frame["month"].between("2023-01-01", "2025-12-01").all()
    assert not t.duplicated(["month", "segment"]).any()


def test_headline_numbers(data):
    k = checkpoints.kpis(data["sales"])
    assert k["Total Sales"] == 301_036_384
    assert k["Total Profit"] == 77_793_572
    assert k["Profit Margin"] == pytest.approx(0.2584, abs=1e-4)
    yv = checkpoints.yearly_vs_plan(data["sales"], data["targets"])
    assert yv.loc[2024, "variance"] == -2_098_069
    mv = checkpoints.market_target(data["sales"], data["targets"])
    assert mv[2024].idxmin() == "Kigali" and mv[2025].idxmin() == "Kigali"


# --------------------------------------------------------------------------- model
def _name(raw):
    raw = raw.strip()
    return raw[1:-1].replace("''", "'") if raw.startswith("'") else raw


@pytest.fixture(scope="module")
def model():
    tables, measures = {}, {}
    for f in (MODEL / "tables").glob("*.tmdl"):
        text = f.read_text(encoding="utf-8")
        table = _name(re.match(r"table (.+)", text).group(1))
        tables[table] = {_name(m) for m in re.findall(r"^\tcolumn (.+)$", text, re.M)}
        for m in re.finditer(r"^\tmeasure ('.+?'|\S+) =(.*?)(?=^\t\t[a-zA-Z]+:)", text, re.M | re.S):
            measures[_name(m.group(1))] = m.group(2)
    return tables, measures


def test_tmdl_uses_tabs_only():
    for f in MODEL.rglob("*.tmdl"):
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            assert not re.match(r"^ +\S", line), f"{f.name}:{i} indented with spaces"
            assert not line.endswith((" ", "\t")), f"{f.name}:{i} trailing whitespace"


def test_star_schema_tables_and_measures(model):
    tables, measures = model
    assert {"Sales", "Targets", "Products", "Markets", "Segment", "Date", "Discount Band"} <= set(tables)
    required = ["Total Sales", "Gross Sales", "Total Discounts", "Discount %", "Total COGS", "Total Profit",
                "Profit Margin", "Units Sold", "Sales Last Year", "Sales Growth %", "Sales YTD",
                "Target Sales", "Variance to Target"]
    assert set(required) <= set(measures)
    assert "SAMEPERIODLASTYEAR" in measures["Sales Last Year"]
    assert "TOTALYTD" in measures["Sales YTD"]


def test_date_table_is_marked_and_covers_2023_to_2025():
    text = (MODEL / "tables" / "Date.tmdl").read_text(encoding="utf-8")
    assert "dataCategory: Time" in text
    assert re.search(r"column Date\n\t\tdataType: dateTime\n\t\tisKey", text)
    assert "CALENDAR ( DATE ( 2023, 1, 1 ), DATE ( 2025, 12, 31 ) )" in text


def test_measure_references_exist(model):
    tables, measures = model
    for name, expr in measures.items():
        body = re.sub(r"--.*", "", expr)
        for ref in re.findall(r"(?<![\w'\]])\[([^\]]+)\]", body):
            assert ref in measures, f"{name} refers to unknown measure [{ref}]"
        for t, c in re.findall(r"'?([A-Za-z][\w ]*?)'?\[([^\]]+)\]", body):
            if t.strip() in tables:
                assert c in tables[t.strip()], f"{name} refers to unknown column {t}[{c}]"


def test_relationships_are_dimension_to_fact(model):
    tables, _ = model
    text = (MODEL / "relationships.tmdl").read_text(encoding="utf-8")
    pairs = re.findall(r"fromColumn: (.+)\n\ttoColumn: (.+)", text)
    assert len(pairs) == 7
    facts, dims = {"Sales", "Targets"}, {"Date", "Segment", "Products", "Markets", "Discount Band"}
    for frm, to in pairs:
        ft, fc = [_name(x) for x in re.match(r"('.+?'|\w+)\.(.+)", frm).groups()]
        tt, tc = [_name(x) for x in re.match(r"('.+?'|\w+)\.(.+)", to).groups()]
        assert ft in facts and tt in dims, f"{frm} -> {to} must go from a fact (many) to a dimension (one)"
        assert fc in tables[ft] and tc in tables[tt]
    assert ("Targets.segment", "Segment.Segment") in pairs and ("Sales.segment", "Segment.Segment") in pairs


# --------------------------------------------------------------------------- report
def _fields(obj):
    if isinstance(obj, dict):
        for kind in ("Measure", "Column"):
            if kind in obj and isinstance(obj[kind], dict) and "Property" in obj[kind]:
                yield kind, obj[kind]["Expression"]["SourceRef"]["Entity"], obj[kind]["Property"]
        for v in obj.values():
            yield from _fields(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _fields(v)


def test_report_pages_and_fields_exist_in_model(model):
    tables, measures = model
    order = json.loads((REPORT / "pages" / "pages.json").read_text())["pageOrder"]
    assert len(order) == 3
    visuals = 0
    for page in order:
        assert (REPORT / "pages" / page / "page.json").exists()
        for vf in (REPORT / "pages" / page / "visuals").glob("*/visual.json"):
            visuals += 1
            for kind, entity, prop in _fields(json.loads(vf.read_text())):
                if kind == "Measure":
                    assert entity == "Key Measures" and prop in measures, f"{vf}: unknown measure {prop}"
                else:
                    assert prop in tables.get(entity, set()), f"{vf}: unknown column {entity}[{prop}]"
    assert visuals >= 20


def test_report_has_required_visuals():
    types = {}
    for vf in REPORT.glob("pages/*/visuals/*/visual.json"):
        v = json.loads(vf.read_text())
        types.setdefault(vf.parts[-4], []).append(v["visual"]["visualType"])
    assert types["overview"].count("card") == 4 and types["overview"].count("slicer") == 3
    assert "lineChart" in types["overview"]
    assert "pivotTable" in types["profit"]
    assert "lineClusteredColumnComboChart" in types["markets"]
