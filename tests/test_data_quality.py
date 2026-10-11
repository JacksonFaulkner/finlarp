import json

import pytest

pytestmark = pytest.mark.integration


def dq(s, focus):
    return json.loads(s.data_quality(focus))[focus]


def test_calendar(s, con):
    c = dq(s, "calendar")
    assert {"days", "first", "last", "half_days", "thin_days"} <= set(c)


def test_docs(s, con):
    assert dq(s, "docs")["views_with_a_model"] >= 8


@pytest.mark.slow
def test_bars(s, con):
    assert dq(s, "bars")["bars_1d"]["malformed"] == 0
