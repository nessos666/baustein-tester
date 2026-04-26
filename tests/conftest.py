from __future__ import annotations
import pandas as pd
import numpy as np
import pytest


@pytest.fixture
def mini_bars() -> pd.DataFrame:
    """100 synthetische 1-Min-Bars mit OHLCV."""
    idx = pd.date_range(
        "2025-01-02 14:00", periods=100, freq="1min", tz="America/New_York"
    )
    rng = np.random.default_rng(42)
    close = 20000.0 + np.cumsum(rng.normal(0, 2, 100))
    df = pd.DataFrame(
        {
            "open": close - 1,
            "high": close + 3,
            "low": close - 3,
            "close": close,
            "volume": rng.integers(100, 500, 100).astype(float),
        },
        index=idx,
    )
    return df


@pytest.fixture
def mini_signals(mini_bars) -> pd.DataFrame:
    """Synthetische Signale: bullish an jedem 10. Bar, bearish an jedem 15. Bar."""
    df = pd.DataFrame(index=mini_bars.index)
    df["breaker_bullish"] = False
    df["breaker_bearish"] = False
    df.iloc[::10, df.columns.get_loc("breaker_bullish")] = True
    df.iloc[::15, df.columns.get_loc("breaker_bearish")] = True
    return df
