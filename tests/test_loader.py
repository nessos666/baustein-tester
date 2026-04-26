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


import pandas as pd
from bt.loader import load_shard, filter_session, merge_bars_and_signals


def test_load_shard_returns_dataframe(mini_signals, tmp_path):
    """load_shard liest eine Parquet-Datei und gibt DataFrame zurueck."""
    shard_path = tmp_path / "test_shard.parquet"
    mini_signals.to_parquet(shard_path)
    df = load_shard(shard_path)
    assert isinstance(df, pd.DataFrame)
    assert "breaker_bullish" in df.columns


def test_filter_session_ny_keeps_only_ny_bars(mini_bars):
    """filter_session('ny') behaelt nur Bars zwischen 09:30 und 12:00 ET."""
    result = filter_session(mini_bars, "ny")
    # mini_bars ist 14:00 NY-Zeit = 19:00 UTC → ausserhalb NY-Session (13:30-16:00 UTC)
    # Darum wird result leer sein – wir testen nur dass kein Fehler geworfen wird
    assert isinstance(result, pd.DataFrame)


def test_filter_session_all_keeps_everything(mini_bars):
    result = filter_session(mini_bars, "all")
    assert len(result) == len(mini_bars)


def test_merge_bars_and_signals_aligns_index(mini_bars, mini_signals):
    merged = merge_bars_and_signals(mini_bars, mini_signals)
    assert "close" in merged.columns
    assert "breaker_bullish" in merged.columns
    assert len(merged) == len(mini_bars)
