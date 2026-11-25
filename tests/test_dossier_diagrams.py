"""Template diagram specs (py/derive/dossier_diagrams.py): picking a non-overlapping member split
and composing a section into beats."""
from derive.dossier_diagrams import compose, partition


def test_partition_drops_parent_member():
    # ASML-shaped: "Product" is the sum of the product lines; Service sits beside them
    items = [["Product", 24474], ["NXE", 10446], ["ArF", 10311], ["Service", 8193], ["EXE", 1157],
             ["KrF", 1001], ["Metrology", 825], ["ArF dry", 427]]
    got = [k for k, _ in partition(items, [32667])]
    assert "Product" not in got and len(got) == 7


def test_partition_picks_one_of_two_side_by_side_splits():
    # VRT-shaped: product/service and ex-spares/services-and-spares both cover revenue
    items = [["Product", 8391], ["Product excluding Spares", 8207], ["Services and Spares", 2023], ["Service", 1839]]
    got = {k for k, _ in partition(items, [10230])}
    assert got in ({"Product", "Service"}, {"Product excluding Spares", "Services and Spares"})


def test_partition_without_total_drops_sum_members():
    items = [["Data Center", 100], ["Compute", 84], ["Networking", 16], ["Gaming", 8]]
    assert [k for k, _ in partition(items, [])] == ["Compute", "Networking", "Gaming"]


def _pts(n, y=100.0):
    return [{"x": f"Q{i}", "y": y + i, "src": {"label": "x"}} for i in range(n)]


def test_compose_financials_falls_back_and_skips_thin_blocks():
    section = {"id": "financials", "blocks": [
        {"type": "series", "title": "Quarterly revenue", "unit": "$M", "points": _pts(2)},  # too few
        {"type": "series", "title": "Annual revenue", "unit": "$M", "points": _pts(5, 1000)},
        {"type": "series", "title": "Operating margin, annual", "unit": "%", "points": _pts(5, -3)},
        {"type": "bars", "title": "Geography (FY ending 2025-12-31)", "unit": "$M",
         "items": [{"label": "US", "value": 600}, {"label": "CN", "value": 404}]},
    ]}
    spec = compose("abc", section)
    assert spec["name"] == "ABC_financials"
    assert [(b["panel"], b["title"]) for b in spec["beats"]] == [
        ("bars", "Annual revenue"), ("bars", "Operating margin, annual"), ("donut", "Geography")]


def test_compose_ignores_tabs_without_a_composition():
    assert compose("ABC", {"id": "news", "blocks": []}) is None
