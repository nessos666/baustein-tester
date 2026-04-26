from bt.concepts import get_columns


def test_breaker_returns_two_columns():
    cols = get_columns("breaker")
    assert cols == ["breaker_bullish", "breaker_bearish"]


def test_bb_alias_same_as_breaker():
    assert get_columns("bb") == get_columns("breaker")


def test_unknown_concept_raises():
    import pytest

    with pytest.raises(ValueError, match="Unbekanntes Konzept"):
        get_columns("xyz_unknown")


def test_case_insensitive():
    assert get_columns("BREAKER") == get_columns("breaker")
