import pytest


@pytest.fixture(scope="module")
def s():
    from agent import server
    return server


@pytest.fixture(scope="module")
def has_data():
    from sources import universe
    root = universe.DATA_ROOT / "market/databento/bars_1m"
    if not any(root.glob("*.parquet")):
        pytest.skip("no bars_1m parquet on disk")
    return True


@pytest.fixture(scope="module")
def con(s, has_data):
    return s._db()
