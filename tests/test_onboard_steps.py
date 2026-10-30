"""The onboard steps for tweet sentiment: present, ordered after tweets, and skipping cleanly without their API keys."""
from jobs import onboard
from sources import keys


def test_steps_are_registered_in_order():
    names = [n for n, _ in onboard.STEPS]
    assert names.index("tweets") < names.index("sentiment") < names.index("bars")
    assert "news" not in names and names[-1] == "dossier"


def test_steps_skip_without_their_keys(monkeypatch):
    monkeypatch.setattr(keys, "get", lambda name: None)
    assert onboard.s_sentiment(["MU"], {}) == "skipped: OPENAI_API_KEY not set"


def test_sentiment_step_skips_when_nothing_is_unlabelled(monkeypatch):
    from sources import tweet_sentiment
    monkeypatch.setattr(keys, "get", lambda name: "k")
    monkeypatch.setattr(tweet_sentiment, "pending", lambda *a, **k: [])
    assert onboard.s_sentiment(["MU"], {}).startswith("skipped: no unlabelled tweets")
