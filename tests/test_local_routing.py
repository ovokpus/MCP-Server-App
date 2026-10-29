"""Unit tests for the local-mode phrase router. No network and no model."""

from api.routing import plan_local_calls


def test_plans_counted_dice() -> None:
    assert plan_local_calls("Roll 2d20k1 for me") == [
        ("roll_dice", {"notation": "2d20k1", "num_rolls": 1})
    ]


def test_plans_bare_die_and_repeats() -> None:
    assert plan_local_calls("Roll a d20 3 times") == [
        ("roll_dice", {"notation": "1d20", "num_rolls": 3})
    ]


def test_caps_repeat_count() -> None:
    calls = plan_local_calls("Roll 1d6 999 times")
    assert calls[0][1]["num_rolls"] == 20


def test_plans_quote_with_theme() -> None:
    calls = plan_local_calls("Create a quote card about shipping software")
    assert calls == [("create_quote_card", {"theme": "shipping software"})]


def test_plans_dice_and_quote_together() -> None:
    names = [name for name, _args in plan_local_calls("Roll 1d4 and create a quote card about courage")]
    assert names == ["roll_dice", "create_quote_card"]


def test_github_search_does_not_also_search_the_web() -> None:
    calls = plan_local_calls("Search GitHub for langgraph")
    assert [name for name, _args in calls] == ["github_search_repositories"]
    assert calls[0][1]["query"] == "langgraph"


def test_web_search_phrase() -> None:
    calls = plan_local_calls("Search the web for the latest AI news")
    assert calls[0][0] == "web_search"
    assert "AI news" in str(calls[0][1]["query"])


def test_unrecognized_message_plans_nothing() -> None:
    assert plan_local_calls("hello there, what can you do?") == []
