from __future__ import annotations
import pandas as pd
import numpy as np
from bt.scanner import scan_concept, ScanResult


def _make_merged(n_bars=200, signal_every=10, seed=42):
    """Hilfsfunktion: merged DataFrame mit synthetischen Daten."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2025-01-02 14:00", periods=n_bars, freq="1min", tz="UTC")
    close = 20000.0 + np.cumsum(rng.normal(0, 2, n_bars))
    df = pd.DataFrame(
        {
            "open": close - 1,
            "high": close + 5,
            "low": close - 5,
            "close": close,
            "bull_signal": False,
            "bear_signal": False,
        },
        index=idx,
    )
    df.iloc[::signal_every, df.columns.get_loc("bull_signal")] = True
    df.iloc[::15, df.columns.get_loc("bear_signal")] = True
    return df


def test_scan_result_has_required_fields():
    merged = _make_merged()
    result = scan_concept(merged, bull_col="bull_signal", bear_col="bear_signal")
    assert isinstance(result, ScanResult)
    assert hasattr(result, "bull_count")
    assert hasattr(result, "bear_count")
    assert hasattr(result, "bull_wr")
    assert hasattr(result, "bear_wr")
    assert hasattr(result, "bull_per_month")
    assert hasattr(result, "bear_per_month")
    assert hasattr(result, "avg_tp_ticks")
    assert hasattr(result, "avg_sl_ticks")


def test_scan_counts_signals_correctly():
    merged = _make_merged(n_bars=200, signal_every=10)
    result = scan_concept(merged, bull_col="bull_signal", bear_col="bear_signal")
    # Alle 10 Bars = 200/10 = 20 bullish Signale
    assert result.bull_count == 20


def test_scan_wr_is_between_0_and_1():
    merged = _make_merged()
    result = scan_concept(merged, bull_col="bull_signal", bear_col="bear_signal")
    assert 0.0 <= result.bull_wr <= 1.0
    assert 0.0 <= result.bear_wr <= 1.0


def test_scan_per_month_positive():
    merged = _make_merged(n_bars=500, signal_every=10)
    result = scan_concept(merged, bull_col="bull_signal", bear_col="bear_signal")
    assert result.bull_per_month > 0
