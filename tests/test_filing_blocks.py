from sources import filing_blocks as fb

# An EDGAR-style income statement: spacer <td/> cells, "$" and ")" split into
# their own cells, header spans, an indented line item, a ruled total, and
# inline XBRL on the values.
INCOME = """
<table>
<tr><td/><td/><td/><td/><td/><td/><td/></tr>
<tr><td/><td colspan="6"><b>Year Ended December 31,</b></td></tr>
<tr><td/><td colspan="3">2025</td><td colspan="3">2024</td></tr>
<tr><td/><td colspan="6">(in millions)</td></tr>
<tr><td>Revenue</td><td>$</td><td><ix:nonFraction name="us-gaap:Revenues">1,200</ix:nonFraction></td><td/>
    <td>$</td><td><ix:nonFraction name="us-gaap:Revenues">900</ix:nonFraction></td><td/></tr>
<tr><td style="padding-left:10pt">Cost of revenue</td><td/><td>(300</td><td>)</td><td/><td>(250</td><td>)</td></tr>
<tr><td style="padding-left:20pt"><b>Gross profit</b></td><td/><td style="border-top:1px solid #000">900</td><td/>
    <td/><td style="border-top:1px solid #000">650</td><td/></tr>
</table>
"""


def _one(html):
    blocks = fb.parse(f"<html><body>{html}</body></html>")
    assert len(blocks) == 1, blocks
    return blocks[0]


def test_income_statement_becomes_a_num_grid():
    t = _one(INCOME)
    assert t["t"] == "table" and t["kind"] == "num"
    assert t["cols"] == 2
    assert t["units"] == "in millions"
    assert t["header"][0] == [{"s": "Year Ended December 31,", "c": 1, "span": 2}]
    assert [c["s"] for c in t["header"][1]] == ["2025", "2024"]
    rev, cost, gross = t["rows"]
    assert rev["label"] == "Revenue"
    assert rev["v"][0] == {"s": "1,200", "cur": "$", "x": "us-gaap:Revenues"}
    assert cost["v"][0]["s"] == "(300)" and cost["v"][0]["neg"] == 1
    assert cost["indent"] == 1 and gross["indent"] == 2
    assert gross["rule"] == "single" and gross["b"] == 1


def test_bullet_table_and_layout_table_unwrap():
    blocks = fb.parse(
        "<html><body>"
        "<table><tr><td>•</td><td>First risk</td></tr></table>"
        "<table><tr><td>•</td><td>Second risk</td></tr></table>"
        "<table><tr><td><p>Just a boxed paragraph of text.</p></td></tr></table>"
        "</body></html>"
    )
    assert [b["t"] for b in blocks] == ["li", "li", "p"]
    assert blocks[0]["spans"] == [{"s": "First risk"}]
    assert blocks[2]["spans"][0]["s"] == "Just a boxed paragraph of text."


def test_headings_items_and_bold_lines():
    blocks = fb.parse(
        "<html><body><p>PART I</p><p><b>Item 1A. Risk Factors</b></p>"
        "<p><b>We may not be profitable.</b></p><p>Body text here.</p></body></html>"
    )
    assert blocks[0] == {"t": "h", "level": 0, "text": "PART I"}
    assert blocks[1]["level"] == 1 and blocks[1]["item"] == "1A"
    assert blocks[2]["t"] == "h" and blocks[2]["level"] == 3
    assert blocks[3] == {"t": "p", "spans": [{"s": "Body text here."}]}


def test_page_break_takes_page_number_and_rejoins_split_paragraph():
    blocks = fb.parse(
        "<html><body><p>Our supply depends on a few</p><p>12</p>"
        '<div style="page-break-after:always"></div>'
        "<p>vendors in Taiwan.</p></body></html>"
    )
    assert blocks[0]["spans"][0]["s"] == "Our supply depends on a few vendors in Taiwan."
    assert blocks[1] == {"t": "page", "n": "12"}


def test_inline_styles_and_textblock_notes():
    blocks = fb.parse(
        '<html><body><ix:nonNumeric name="us-gaap:LeasesTextBlock">'
        "<p>We lease <i>offices</i> and <b>data centers</b>.</p></ix:nonNumeric></body></html>"
    )
    assert blocks[0] == {"t": "note", "concept": "us-gaap:LeasesTextBlock"}
    assert blocks[1]["spans"] == [
        {"s": "We lease "}, {"s": "offices", "i": 1}, {"s": " and "}, {"s": "data centers", "b": 1}, {"s": "."},
    ]


def test_hidden_header_is_skipped():
    blocks = fb.parse(
        '<html><body><div style="display:none"><ix:header>dei facts</ix:header>secret</div>'
        "<p>Visible.</p></body></html>"
    )
    assert blocks == [{"t": "p", "spans": [{"s": "Visible."}]}]
