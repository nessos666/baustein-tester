from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

_LOOKFORWARD_BARS = 50
_TP_TICKS = 10
_SL_TICKS = 10
_TICK_SIZE = 0.25  # MNQ: 0.25 Punkte = 1 Tick


@dataclass
class ScanResult:
    concept: str
    session: str
    total_bars: int
    date_from: str
    date_to: str
    bull_count: int
    bull_per_month: float
    bull_wr: float
    avg_tp_ticks: float
    avg_sl_ticks: float
    bear_count: int
    bear_per_month: float
    bear_wr: float


def _simulate_entries(
    merged: pd.DataFrame,
    signal_col: str,
    direction: str,
    tp_ticks: int = _TP_TICKS,
    sl_ticks: int = _SL_TICKS,
    lookforward: int = _LOOKFORWARD_BARS,
) -> tuple[float, float, float]:
    highs = merged["high"].values
    lows = merged["low"].values
    opens = merged["open"].values
    signal = merged[signal_col].values
    n = len(merged)

    wins = 0
    losses = 0
    tp_dist: list[float] = []
    sl_dist: list[float] = []

    tp_pts = tp_ticks * _TICK_SIZE
    sl_pts = sl_ticks * _TICK_SIZE

    for i in range(n - 1):
        if not signal[i]:
            continue
        entry = opens[i + 1]
        tp = entry + tp_pts if direction == "long" else entry - tp_pts
        sl = entry - sl_pts if direction == "long" else entry + sl_pts

        hit = False
        for j in range(i + 1, min(i + 1 + lookforward, n)):
            h, l = highs[j], lows[j]
            if direction == "long":
                if l <= sl:
                    losses += 1
                    sl_dist.append(sl_pts / _TICK_SIZE)
                    hit = True
                    break
                if h >= tp:
                    wins += 1
                    tp_dist.append(tp_pts / _TICK_SIZE)
                    hit = True
                    break
            else:
                if h >= sl:
                    losses += 1
                    sl_dist.append(sl_pts / _TICK_SIZE)
                    hit = True
                    break
                if l <= tp:
                    wins += 1
                    tp_dist.append(tp_pts / _TICK_SIZE)
                    hit = True
                    break
        if not hit:
            losses += 1

    total = wins + losses
    wr = wins / total if total > 0 else 0.0
    avg_tp = float(np.mean(tp_dist)) if tp_dist else 0.0
    avg_sl = float(np.mean(sl_dist)) if sl_dist else 0.0
    return wr, avg_tp, avg_sl


def _months_in_df(df: pd.DataFrame) -> float:
    if len(df) == 0:
        return 1.0
    delta = df.index[-1] - df.index[0]
    return max(delta.days / 30.44, 1.0)


def scan_concept(
    merged: pd.DataFrame,
    bull_col: str,
    bear_col: str,
    concept: str = "unknown",
    session: str = "all",
    tp_ticks: int = _TP_TICKS,
    sl_ticks: int = _SL_TICKS,
) -> ScanResult:
    months = _months_in_df(merged)
    bull_count = int(merged[bull_col].sum()) if bull_col in merged.columns else 0
    bear_count = int(merged[bear_col].sum()) if bear_col in merged.columns else 0

    bull_wr, avg_tp, avg_sl = 0.0, 0.0, 0.0
    if bull_count > 0 and bull_col in merged.columns:
        bull_wr, avg_tp, avg_sl = _simulate_entries(
            merged, bull_col, "long", tp_ticks, sl_ticks
        )

    bear_wr = 0.0
    if bear_count > 0 and bear_col in merged.columns:
        bear_wr, _, _ = _simulate_entries(merged, bear_col, "short", tp_ticks, sl_ticks)

    date_from = str(merged.index.min().date()) if len(merged) > 0 else ""
    date_to = str(merged.index.max().date()) if len(merged) > 0 else ""

    return ScanResult(
        concept=concept,
        session=session,
        total_bars=len(merged),
        date_from=date_from,
        date_to=date_to,
        bull_count=bull_count,
        bull_per_month=round(bull_count / months, 1),
        bull_wr=round(bull_wr, 4),
        avg_tp_ticks=round(avg_tp, 1),
        avg_sl_ticks=round(avg_sl, 1),
        bear_count=bear_count,
        bear_per_month=round(bear_count / months, 1),
        bear_wr=round(bear_wr, 4),
    )
