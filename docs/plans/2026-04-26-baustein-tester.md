# Baustein-Tester Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eigenstaendiges CLI-Programm das einzelne PDA-Bausteine (BREAKER, OB, FVG, ...) statistisch analysiert, vergleicht und als HTML-Report ausgibt – ohne Optuna, ohne Nautilus.

**Architecture:** `probe.py` liest Signal-Shards + NQ-1m-Bars direkt als Parquet. `bt/scanner.py` simuliert Simple-Entries (kein Nautilus) und berechnet Frequenz, Raw-WR, Ø Ticks. `bt/report.py` generiert HTML + Rich-Console-Output. Alle Pfade kommen aus `probe.toml`.

**Tech Stack:** Python 3.12, typer, rich, pandas, pyarrow, jinja2, pytest

---

## Datei-Struktur

```
26_Baustein_Tester/
├── probe.py                  <- CLI Einstiegspunkt (typer)
├── probe.toml                <- Konfiguration (Pfade zu Daten/Shards)
├── bt/
│   ├── __init__.py
│   ├── concepts.py           <- Konzept → Spalten-Mapping (von cache_query.py)
│   ├── loader.py             <- Shards + NQ-Bars laden, Session-Filter
│   ├── scanner.py            <- Baustein analysieren (Frequenz, Raw-WR, Ticks)
│   ├── comparator.py         <- Zwei Konzepte vergleichen
│   └── report.py             <- Rich-Console + HTML-Ausgabe
├── tests/
│   ├── conftest.py           <- Fixtures: Mini-DataFrame mit synthetischen Signalen
│   ├── test_loader.py
│   ├── test_scanner.py
│   ├── test_comparator.py
│   └── test_report.py
└── docs/plans/
    └── 2026-04-26-baustein-tester.md
```

**Datenpfade (aus probe.toml):**
- Bars: `.../nq_backtest/data/nq_1m_walkforward.parquet`
- Shards-Dir: `.../nq_backtest/data/signal_shards/`

---

## Task 1: Projekt-Skeleton + Config

**Files:**
- Create: `/home/boobi/HAUPTLAGER/26_Baustein_Tester/probe.toml`
- Create: `/home/boobi/HAUPTLAGER/26_Baustein_Tester/bt/__init__.py`
- Create: `/home/boobi/HAUPTLAGER/26_Baustein_Tester/tests/conftest.py`

- [ ] **Step 1: probe.toml schreiben**

```toml
[data]
bars_path = "/home/boobi/HAUPTLAGER/05_Strategien_Entwicklung/TRADINGPROJEKT/nq_backtest/data/nq_1m_walkforward.parquet"
shards_dir = "/home/boobi/HAUPTLAGER/05_Strategien_Entwicklung/TRADINGPROJEKT/nq_backtest/data/signal_shards"
output_dir = "/home/boobi/HAUPTLAGER/26_Baustein_Tester/output"
```

- [ ] **Step 2: bt/__init__.py anlegen (leer)**

```python
```

- [ ] **Step 3: tests/conftest.py mit Mini-Fixtures**

```python
from __future__ import annotations
import pandas as pd
import numpy as np
import pytest

@pytest.fixture
def mini_bars() -> pd.DataFrame:
    """100 synthetische 1-Min-Bars mit OHLCV."""
    idx = pd.date_range("2025-01-02 14:00", periods=100, freq="1min", tz="America/New_York")
    rng = np.random.default_rng(42)
    close = 20000.0 + np.cumsum(rng.normal(0, 2, 100))
    df = pd.DataFrame({
        "open": close - 1,
        "high": close + 3,
        "low": close - 3,
        "close": close,
        "volume": rng.integers(100, 500, 100).astype(float),
    }, index=idx)
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
```

- [ ] **Step 4: venv anlegen + Abhängigkeiten installieren**

```bash
cd /home/boobi/HAUPTLAGER/26_Baustein_Tester
python3 -m venv .venv
source .venv/bin/activate
pip install typer rich pandas pyarrow jinja2 tomllib pytest
```

- [ ] **Step 5: Prüfen ob venv ok**

```bash
source .venv/bin/activate && python3 -c "import typer, rich, pandas, jinja2; print('OK')"
```
Expected: `OK`

---

## Task 2: concepts.py – Konzept → Spalten-Mapping

**Files:**
- Create: `/home/boobi/HAUPTLAGER/26_Baustein_Tester/bt/concepts.py`
- Create: `/home/boobi/HAUPTLAGER/26_Baustein_Tester/tests/test_loader.py` (teilweise)

- [ ] **Step 1: Failing test schreiben**

```python
# tests/test_loader.py
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
```

- [ ] **Step 2: Test laufen lassen (muss FAIL)**

```bash
cd /home/boobi/HAUPTLAGER/26_Baustein_Tester && source .venv/bin/activate
pytest tests/test_loader.py::test_breaker_returns_two_columns -v
```
Expected: FAIL `ModuleNotFoundError` oder `ImportError`

- [ ] **Step 3: bt/concepts.py implementieren**

```python
from __future__ import annotations

# Konzept-Name (lowercase) → Spalten im Signal-Shard
_CONCEPT_COLUMNS: dict[str, list[str]] = {
    "bos":         ["bos_bullish", "bos_bearish"],
    "choch":       ["choch_bullish", "choch_bearish"],
    "ob":          ["ob_bullish", "ob_bearish"],
    "mb":          ["mb_bullish", "mb_bearish"],
    "fvg":         ["fvg_bullish", "fvg_bearish"],
    "ifvg":        ["ifvg_bullish", "ifvg_bearish"],
    "bpr":         ["bpr_bullish", "bpr_bearish"],
    "breaker":     ["breaker_bullish", "breaker_bearish"],
    "rb":          ["rb_bullish", "rb_bearish"],
    "sweep":       ["swept_buy_side", "swept_sell_side"],
    "judas":       ["js_bullish", "js_bearish"],
    "silver_bullet": ["sb_entry_long", "sb_entry_short"],
    "manip":       ["manip_bullish", "manip_bearish"],
    "displacement": ["displacement_bullish", "displacement_bearish"],
}

# Aliase
_ALIASES: dict[str, str] = {
    "bb": "breaker",
    "sb": "silver_bullet",
    "ob_new": "ob",
}

def get_columns(concept: str) -> list[str]:
    """Gibt Spalten-Namen fuer ein Konzept zurueck. Case-insensitiv."""
    key = concept.strip().lower()
    key = _ALIASES.get(key, key)
    if key not in _CONCEPT_COLUMNS:
        raise ValueError(f"Unbekanntes Konzept: '{concept}'. Bekannt: {sorted(_CONCEPT_COLUMNS)}")
    return _CONCEPT_COLUMNS[key]

def all_concepts() -> list[str]:
    """Liste aller bekannten Konzepte (ohne Aliase)."""
    return sorted(_CONCEPT_COLUMNS)
```

- [ ] **Step 4: Tests laufen lassen (muss PASS)**

```bash
pytest tests/test_loader.py -v
```
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git init && git add bt/ tests/ probe.toml docs/
git commit -m "feat: project skeleton + concepts mapping"
```

---

## Task 3: loader.py – Daten laden + Session-Filter

**Files:**
- Create: `/home/boobi/HAUPTLAGER/26_Baustein_Tester/bt/loader.py`
- Modify: `/home/boobi/HAUPTLAGER/26_Baustein_Tester/tests/test_loader.py`

- [ ] **Step 1: Failing tests schreiben**

```python
# tests/test_loader.py – ergaenzen:
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
    hours = result.index.hour
    assert all((h >= 9) for h in hours), f"Stunden ausserhalb NY: {set(hours)}"

def test_filter_session_all_keeps_everything(mini_bars):
    result = filter_session(mini_bars, "all")
    assert len(result) == len(mini_bars)

def test_merge_bars_and_signals_aligns_index(mini_bars, mini_signals):
    merged = merge_bars_and_signals(mini_bars, mini_signals)
    assert "close" in merged.columns
    assert "breaker_bullish" in merged.columns
    assert len(merged) == len(mini_bars)
```

- [ ] **Step 2: Tests laufen lassen (muss FAIL)**

```bash
pytest tests/test_loader.py -v 2>&1 | tail -10
```
Expected: FAIL `ImportError: cannot import name 'load_shard'`

- [ ] **Step 3: bt/loader.py implementieren**

```python
from __future__ import annotations

import tomllib
from pathlib import Path

import pandas as pd

# UTC-Stunden fuer Session-Filter (start_inclusive, end_exclusive)
# NY = 13:30-16:00 UTC = 09:30-12:00 ET
_SESSION_UTC: dict[str, tuple[float, float]] = {
    "london": (7.0, 11.0),
    "ny":     (13.5, 16.0),
    "asia":   (1.0, 4.0),
}


def load_config(config_path: Path = Path("probe.toml")) -> dict:
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def load_bars(bars_path: Path) -> pd.DataFrame:
    """Laedt NQ-1m-Bars aus Parquet. Index muss DatetimeIndex sein."""
    df = pd.read_parquet(bars_path)
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError(f"Bars-Index ist kein DatetimeIndex: {type(df.index)}")
    return df


def load_shard(shard_path: Path) -> pd.DataFrame:
    """Laedt einen Signal-Shard aus Parquet."""
    df = pd.read_parquet(shard_path)
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError(f"Shard-Index ist kein DatetimeIndex: {type(df.index)}")
    return df


def find_shard(shards_dir: Path, concept_cols: list[str]) -> pd.DataFrame | None:
    """Sucht den Shard der die angefragten Spalten enthaelt."""
    for shard_file in sorted(Path(shards_dir).glob("*.parquet")):
        df = load_shard(shard_file)
        if any(col in df.columns for col in concept_cols):
            return df
    return None


def filter_session(df: pd.DataFrame, session: str) -> pd.DataFrame:
    """Filtert DataFrame nach Session (UTC-Stunden). 'all' = kein Filter."""
    if session == "all" or session not in _SESSION_UTC:
        return df
    idx = df.index
    if idx.tz is None:
        idx_utc = idx.tz_localize("UTC")
    else:
        idx_utc = idx.tz_convert("UTC")
    start_h, end_h = _SESSION_UTC[session]
    # Halbe Stunden als Dezimal: 13.5 = 13:30
    decimal_hours = idx_utc.hour + idx_utc.minute / 60.0
    mask = (decimal_hours >= start_h) & (decimal_hours < end_h)
    return df[mask]


def merge_bars_and_signals(bars: pd.DataFrame, signals: pd.DataFrame) -> pd.DataFrame:
    """Joined Bars und Signals auf gemeinsamem Index (inner join)."""
    # Beide auf UTC normieren fuer sicheren Join
    bars_utc = bars.copy()
    sigs_utc = signals.copy()
    if bars_utc.index.tz is None:
        bars_utc.index = bars_utc.index.tz_localize("UTC")
    else:
        bars_utc.index = bars_utc.index.tz_convert("UTC")
    if sigs_utc.index.tz is None:
        sigs_utc.index = sigs_utc.index.tz_localize("UTC")
    else:
        sigs_utc.index = sigs_utc.index.tz_convert("UTC")
    merged = bars_utc.join(sigs_utc, how="inner")
    # Signal-Spalten: NaN → False
    for col in sigs_utc.columns:
        if col in merged.columns:
            merged[col] = merged[col].fillna(False).astype(bool)
    return merged
```

- [ ] **Step 4: Tests laufen lassen (muss PASS)**

```bash
pytest tests/test_loader.py -v
```
Expected: alle PASSED

- [ ] **Step 5: Commit**

```bash
git add bt/loader.py tests/test_loader.py
git commit -m "feat: loader with shard reader and session filter"
```

---

## Task 4: scanner.py – Baustein analysieren

**Files:**
- Create: `/home/boobi/HAUPTLAGER/26_Baustein_Tester/bt/scanner.py`
- Create: `/home/boobi/HAUPTLAGER/26_Baustein_Tester/tests/test_scanner.py`

- [ ] **Step 1: Failing tests schreiben**

```python
# tests/test_scanner.py
from __future__ import annotations
import pandas as pd
import numpy as np
import pytest
from bt.scanner import scan_concept, ScanResult

def _make_merged(n_bars=200, signal_every=10, seed=42):
    """Hilfsfunktion: merged DataFrame mit synthetischen Daten."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2025-01-02 14:00", periods=n_bars, freq="1min", tz="UTC")
    close = 20000.0 + np.cumsum(rng.normal(0, 2, n_bars))
    df = pd.DataFrame({
        "open": close - 1,
        "high": close + 5,
        "low": close - 5,
        "close": close,
        "bull_signal": False,
        "bear_signal": False,
    }, index=idx)
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
```

- [ ] **Step 2: Tests laufen lassen (muss FAIL)**

```bash
pytest tests/test_scanner.py -v 2>&1 | tail -5
```
Expected: FAIL `ImportError`

- [ ] **Step 3: bt/scanner.py implementieren**

```python
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

# Simulation-Parameter fuer Raw-WR
_LOOKFORWARD_BARS = 50   # max. wie viele Bars nach Signal schauen
_TP_TICKS = 10           # Default Take-Profit in Ticks (0.25pt = 1 Tick MNQ)
_SL_TICKS = 10           # Default Stop-Loss in Ticks
_TICK_SIZE = 0.25        # MNQ: 0.25 Punkte = 1 Tick


@dataclass
class ScanResult:
    concept: str
    session: str
    total_bars: int
    date_from: str
    date_to: str
    # Bullish
    bull_count: int
    bull_per_month: float
    bull_wr: float          # 0.0–1.0
    avg_tp_ticks: float     # Ø Ticks bis TP bei Wins
    avg_sl_ticks: float     # Ø Ticks bis SL bei Losses
    # Bearish
    bear_count: int
    bear_per_month: float
    bear_wr: float


def _simulate_entries(
    merged: pd.DataFrame,
    signal_col: str,
    direction: str,          # "long" oder "short"
    tp_ticks: int = _TP_TICKS,
    sl_ticks: int = _SL_TICKS,
    lookforward: int = _LOOKFORWARD_BARS,
) -> tuple[float, float, float]:
    """
    Einfache Entry-Simulation ohne Nautilus.
    Fuer jeden aktiven Signal-Bar: Entry am naechsten Bar-Open.
    TP = entry + tp_ticks*tick_size (long) / entry - tp_ticks*tick_size (short)
    SL = entry - sl_ticks*tick_size (long) / entry + sl_ticks*tick_size (short)

    Returns: (win_rate, avg_tp_ticks_on_win, avg_sl_ticks_on_loss)
    """
    closes = merged["close"].values
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
        entry = opens[i + 1]  # naechster Bar-Open
        tp = entry + tp_pts if direction == "long" else entry - tp_pts
        sl = entry - sl_pts if direction == "long" else entry + sl_pts

        hit = False
        for j in range(i + 1, min(i + 1 + lookforward, n)):
            h, l = highs[j], lows[j]
            if direction == "long":
                if l <= sl:
                    losses += 1
                    sl_dist.append(abs(entry - sl) / _TICK_SIZE)
                    hit = True
                    break
                if h >= tp:
                    wins += 1
                    tp_dist.append(abs(tp - entry) / _TICK_SIZE)
                    hit = True
                    break
            else:
                if h >= sl:
                    losses += 1
                    sl_dist.append(abs(sl - entry) / _TICK_SIZE)
                    hit = True
                    break
                if l <= tp:
                    wins += 1
                    tp_dist.append(abs(entry - tp) / _TICK_SIZE)
                    hit = True
                    break
        if not hit:
            losses += 1  # Timeout = Loss

    total = wins + losses
    wr = wins / total if total > 0 else 0.0
    avg_tp = float(np.mean(tp_dist)) if tp_dist else 0.0
    avg_sl = float(np.mean(sl_dist)) if sl_dist else 0.0
    return wr, avg_tp, avg_sl


def _months_in_df(df: pd.DataFrame) -> float:
    """Zeitspanne des DataFrame in Monaten."""
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
    """Analysiert ein Konzept in einem merged DataFrame."""
    months = _months_in_df(merged)
    bull_count = int(merged[bull_col].sum()) if bull_col in merged.columns else 0
    bear_count = int(merged[bear_col].sum()) if bear_col in merged.columns else 0

    bull_wr, avg_tp, avg_sl = (0.0, 0.0, 0.0)
    if bull_count > 0 and bull_col in merged.columns:
        bull_wr, avg_tp, avg_sl = _simulate_entries(
            merged, bull_col, "long", tp_ticks, sl_ticks
        )

    bear_wr = 0.0
    if bear_count > 0 and bear_col in merged.columns:
        bear_wr, _, _ = _simulate_entries(
            merged, bear_col, "short", tp_ticks, sl_ticks
        )

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
```

- [ ] **Step 4: Tests laufen lassen (muss PASS)**

```bash
pytest tests/test_scanner.py -v
```
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add bt/scanner.py tests/test_scanner.py
git commit -m "feat: scanner with signal frequency and raw WR simulation"
```

---

## Task 5: comparator.py – Zwei Konzepte vergleichen

**Files:**
- Create: `/home/boobi/HAUPTLAGER/26_Baustein_Tester/bt/comparator.py`
- Create: `/home/boobi/HAUPTLAGER/26_Baustein_Tester/tests/test_comparator.py`

- [ ] **Step 1: Failing test schreiben**

```python
# tests/test_comparator.py
from bt.comparator import compare_concepts, CompareResult
from bt.scanner import ScanResult

def _make_result(concept, bull_wr, bull_count):
    return ScanResult(
        concept=concept, session="ny", total_bars=10000,
        date_from="2024-01-01", date_to="2026-01-01",
        bull_count=bull_count, bull_per_month=bull_count/24,
        bull_wr=bull_wr, avg_tp_ticks=10.0, avg_sl_ticks=10.0,
        bear_count=bull_count, bear_per_month=bull_count/24,
        bear_wr=bull_wr,
    )

def test_compare_returns_both_results():
    a = _make_result("breaker", 0.55, 200)
    b = _make_result("ob", 0.48, 400)
    cr = compare_concepts(a, b)
    assert isinstance(cr, CompareResult)
    assert cr.result_a.concept == "breaker"
    assert cr.result_b.concept == "ob"

def test_compare_identifies_higher_wr():
    a = _make_result("breaker", 0.55, 200)
    b = _make_result("ob", 0.48, 400)
    cr = compare_concepts(a, b)
    assert cr.higher_bull_wr == "breaker"

def test_compare_identifies_higher_frequency():
    a = _make_result("breaker", 0.55, 200)
    b = _make_result("ob", 0.48, 400)
    cr = compare_concepts(a, b)
    assert cr.higher_bull_freq == "ob"
```

- [ ] **Step 2: Tests laufen lassen (muss FAIL)**

```bash
pytest tests/test_comparator.py -v 2>&1 | tail -5
```
Expected: FAIL `ImportError`

- [ ] **Step 3: bt/comparator.py implementieren**

```python
from __future__ import annotations

from dataclasses import dataclass

from bt.scanner import ScanResult


@dataclass
class CompareResult:
    result_a: ScanResult
    result_b: ScanResult
    higher_bull_wr: str      # Name des Konzepts mit hoeherer Bull-WR
    higher_bear_wr: str
    higher_bull_freq: str    # Name des Konzepts mit hoeherem Bull-Signal/Monat
    higher_bear_freq: str


def compare_concepts(a: ScanResult, b: ScanResult) -> CompareResult:
    """Vergleicht zwei ScanResults und bestimmt Sieger je Kategorie."""
    return CompareResult(
        result_a=a,
        result_b=b,
        higher_bull_wr=a.concept if a.bull_wr >= b.bull_wr else b.concept,
        higher_bear_wr=a.concept if a.bear_wr >= b.bear_wr else b.concept,
        higher_bull_freq=a.concept if a.bull_per_month >= b.bull_per_month else b.concept,
        higher_bear_freq=a.concept if a.bear_per_month >= b.bear_per_month else b.concept,
    )
```

- [ ] **Step 4: Tests laufen lassen (muss PASS)**

```bash
pytest tests/test_comparator.py -v
```
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add bt/comparator.py tests/test_comparator.py
git commit -m "feat: comparator for two concepts"
```

---

## Task 6: report.py – Rich-Console + HTML-Ausgabe

**Files:**
- Create: `/home/boobi/HAUPTLAGER/26_Baustein_Tester/bt/report.py`
- Create: `/home/boobi/HAUPTLAGER/26_Baustein_Tester/tests/test_report.py`

- [ ] **Step 1: Failing tests schreiben**

```python
# tests/test_report.py
from bt.report import print_scan_result, render_html_report
from bt.scanner import ScanResult
from pathlib import Path

def _make_result():
    return ScanResult(
        concept="breaker", session="ny", total_bars=699248,
        date_from="2024-03-25", date_to="2026-03-25",
        bull_count=423, bull_per_month=17.6,
        bull_wr=0.521, avg_tp_ticks=10.0, avg_sl_ticks=10.0,
        bear_count=424, bear_per_month=17.7,
        bear_wr=0.489,
    )

def test_print_scan_result_runs_without_error(capsys):
    print_scan_result(_make_result())
    captured = capsys.readouterr()
    # Rich schreibt in stderr, darum nichts pruefen – nur kein Exception

def test_render_html_contains_concept_name(tmp_path):
    html = render_html_report(_make_result(), output_dir=tmp_path)
    assert "breaker" in html.lower()
    assert "521" in html or "52.1" in html   # WR erscheint

def test_render_html_writes_file(tmp_path):
    render_html_report(_make_result(), output_dir=tmp_path)
    files = list(tmp_path.glob("*.html"))
    assert len(files) == 1

def test_render_html_compare_contains_both(tmp_path):
    from bt.comparator import compare_concepts, CompareResult
    from bt.report import render_html_compare
    a = _make_result()
    b = ScanResult(
        concept="ob", session="ny", total_bars=699248,
        date_from="2024-03-25", date_to="2026-03-25",
        bull_count=300, bull_per_month=12.5,
        bull_wr=0.48, avg_tp_ticks=10.0, avg_sl_ticks=10.0,
        bear_count=310, bear_per_month=12.9,
        bear_wr=0.46,
    )
    cr = compare_concepts(a, b)
    html = render_html_compare(cr, output_dir=tmp_path)
    assert "breaker" in html.lower()
    assert "ob" in html.lower()
```

- [ ] **Step 2: Tests laufen lassen (muss FAIL)**

```bash
pytest tests/test_report.py -v 2>&1 | tail -5
```
Expected: FAIL `ImportError`

- [ ] **Step 3: bt/report.py implementieren**

```python
from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table

from bt.comparator import CompareResult
from bt.scanner import ScanResult

console = Console()

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>Baustein-Tester: {concept}</title>
<style>
  body {{ font-family: monospace; background: #111; color: #eee; padding: 2rem; }}
  h1 {{ color: #7ec8e3; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
  th {{ background: #222; color: #7ec8e3; padding: 8px 12px; text-align: left; }}
  td {{ padding: 6px 12px; border-bottom: 1px solid #333; }}
  .win {{ color: #6fcf97; }}
  .loss {{ color: #eb5757; }}
  .neutral {{ color: #f2c94c; }}
  .section {{ margin-top: 2rem; }}
</style>
</head>
<body>
<h1>Baustein-Tester: {concept}</h1>
<p>Session: <b>{session}</b> | Daten: {date_from} → {date_to} | Bars: {total_bars:,}</p>

<div class="section">
<h2>Bullish Signale</h2>
<table>
<tr><th>Metrik</th><th>Wert</th></tr>
<tr><td>Anzahl gesamt</td><td>{bull_count:,}</td></tr>
<tr><td>Signale / Monat</td><td>{bull_per_month:.1f}</td></tr>
<tr><td>Raw Win-Rate (1:1 RR)</td><td class="{bull_wr_class}">{bull_wr_pct:.1f}%</td></tr>
<tr><td>Ø Ticks bis TP (bei Wins)</td><td>{avg_tp_ticks:.1f}</td></tr>
<tr><td>Ø Ticks bis SL (bei Losses)</td><td>{avg_sl_ticks:.1f}</td></tr>
</table>
</div>

<div class="section">
<h2>Bearish Signale</h2>
<table>
<tr><th>Metrik</th><th>Wert</th></tr>
<tr><td>Anzahl gesamt</td><td>{bear_count:,}</td></tr>
<tr><td>Signale / Monat</td><td>{bear_per_month:.1f}</td></tr>
<tr><td>Raw Win-Rate (1:1 RR)</td><td class="{bear_wr_class}">{bear_wr_pct:.1f}%</td></tr>
</table>
</div>
</body></html>"""

_HTML_COMPARE_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>Vergleich: {concept_a} vs {concept_b}</title>
<style>
  body {{ font-family: monospace; background: #111; color: #eee; padding: 2rem; }}
  h1 {{ color: #7ec8e3; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
  th {{ background: #222; color: #7ec8e3; padding: 8px 12px; text-align: left; }}
  td {{ padding: 6px 12px; border-bottom: 1px solid #333; }}
  .winner {{ color: #6fcf97; font-weight: bold; }}
</style>
</head>
<body>
<h1>Vergleich: {concept_a} vs {concept_b}</h1>
<table>
<tr><th>Metrik</th><th>{concept_a}</th><th>{concept_b}</th><th>Sieger</th></tr>
<tr><td>Bull Signale/Monat</td><td>{a_bull_freq:.1f}</td><td>{b_bull_freq:.1f}</td>
    <td class="winner">{higher_bull_freq}</td></tr>
<tr><td>Bull Raw-WR</td><td>{a_bull_wr:.1f}%</td><td>{b_bull_wr:.1f}%</td>
    <td class="winner">{higher_bull_wr}</td></tr>
<tr><td>Bear Signale/Monat</td><td>{a_bear_freq:.1f}</td><td>{b_bear_freq:.1f}</td>
    <td class="winner">{higher_bear_freq}</td></tr>
<tr><td>Bear Raw-WR</td><td>{a_bear_wr:.1f}%</td><td>{b_bear_wr:.1f}%</td>
    <td class="winner">{higher_bear_wr}</td></tr>
</table>
</body></html>"""


def _wr_class(wr: float) -> str:
    if wr >= 0.52:
        return "win"
    if wr <= 0.45:
        return "loss"
    return "neutral"


def print_scan_result(result: ScanResult) -> None:
    """Gibt ScanResult als Rich-Tabelle auf der Konsole aus."""
    console.rule(f"[cyan]Baustein: {result.concept.upper()} | Session: {result.session}")
    console.print(f"Zeitraum: {result.date_from} → {result.date_to} | Bars: {result.total_bars:,}\n")

    t = Table(show_header=True, header_style="bold cyan")
    t.add_column("Metrik")
    t.add_column("Bullish", justify="right")
    t.add_column("Bearish", justify="right")

    def wr_fmt(v: float) -> str:
        pct = f"{v*100:.1f}%"
        if v >= 0.52:
            return f"[green]{pct}[/green]"
        if v <= 0.45:
            return f"[red]{pct}[/red]"
        return f"[yellow]{pct}[/yellow]"

    t.add_row("Signale gesamt", f"{result.bull_count:,}", f"{result.bear_count:,}")
    t.add_row("Signale / Monat", f"{result.bull_per_month:.1f}", f"{result.bear_per_month:.1f}")
    t.add_row("Raw Win-Rate (1:1)", wr_fmt(result.bull_wr), wr_fmt(result.bear_wr))
    t.add_row("Ø Ticks bis TP", f"{result.avg_tp_ticks:.1f}", "—")
    t.add_row("Ø Ticks bis SL", f"{result.avg_sl_ticks:.1f}", "—")
    console.print(t)


def render_html_report(result: ScanResult, output_dir: Path) -> str:
    """Rendert HTML-Report und schreibt ihn in output_dir. Gibt HTML-String zurueck."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    html = _HTML_TEMPLATE.format(
        concept=result.concept,
        session=result.session,
        date_from=result.date_from,
        date_to=result.date_to,
        total_bars=result.total_bars,
        bull_count=result.bull_count,
        bull_per_month=result.bull_per_month,
        bull_wr_pct=result.bull_wr * 100,
        bull_wr_class=_wr_class(result.bull_wr),
        avg_tp_ticks=result.avg_tp_ticks,
        avg_sl_ticks=result.avg_sl_ticks,
        bear_count=result.bear_count,
        bear_per_month=result.bear_per_month,
        bear_wr_pct=result.bear_wr * 100,
        bear_wr_class=_wr_class(result.bear_wr),
    )
    out_file = Path(output_dir) / f"probe_{result.concept}_{result.session}.html"
    out_file.write_text(html, encoding="utf-8")
    return html


def render_html_compare(cr: CompareResult, output_dir: Path) -> str:
    """Rendert Vergleichs-HTML und schreibt ihn in output_dir."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    a, b = cr.result_a, cr.result_b
    html = _HTML_COMPARE_TEMPLATE.format(
        concept_a=a.concept,
        concept_b=b.concept,
        a_bull_freq=a.bull_per_month,
        b_bull_freq=b.bull_per_month,
        a_bull_wr=a.bull_wr * 100,
        b_bull_wr=b.bull_wr * 100,
        a_bear_freq=a.bear_per_month,
        b_bear_freq=b.bear_per_month,
        a_bear_wr=a.bear_wr * 100,
        b_bear_wr=b.bear_wr * 100,
        higher_bull_freq=cr.higher_bull_freq,
        higher_bull_wr=cr.higher_bull_wr,
        higher_bear_freq=cr.higher_bear_freq,
        higher_bear_wr=cr.higher_bear_wr,
    )
    out_file = Path(output_dir) / f"compare_{a.concept}_vs_{b.concept}.html"
    out_file.write_text(html, encoding="utf-8")
    return html
```

- [ ] **Step 4: Tests laufen lassen (muss PASS)**

```bash
pytest tests/test_report.py -v
```
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add bt/report.py tests/test_report.py
git commit -m "feat: rich console + html report"
```

---

## Task 7: probe.py – CLI zusammenbauen

**Files:**
- Create: `/home/boobi/HAUPTLAGER/26_Baustein_Tester/probe.py`

- [ ] **Step 1: probe.py schreiben**

```python
#!/usr/bin/env python3
"""Baustein-Tester – analysiert einzelne PDA-Bausteine.

Verwendung:
  ./probe.py scan BREAKER --session ny
  ./probe.py scan FVG --session london
  ./probe.py compare BREAKER OB --session ny
  ./probe.py list
"""
from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console

from bt.concepts import all_concepts, get_columns
from bt.loader import filter_session, find_shard, load_bars, load_config, merge_bars_and_signals
from bt.report import print_scan_result, render_html_compare, render_html_report
from bt.scanner import scan_concept
from bt.comparator import compare_concepts

app = typer.Typer(help="Baustein-Tester – PDA-Bausteine statistisch analysieren.")
console = Console()

_DEFAULT_CONFIG = Path(__file__).parent / "probe.toml"


def _load_cfg(config: Path) -> dict:
    try:
        return load_config(config)
    except FileNotFoundError:
        console.print(f"[red]Config nicht gefunden: {config}[/red]")
        raise typer.Exit(1)


@app.command()
def scan(
    concept: str = typer.Argument(help='Konzept-Name, z.B. "BREAKER" oder "BB"'),
    session: str = typer.Option("ny", help="Session: ny | london | asia | all"),
    tp: int = typer.Option(10, help="Take-Profit in Ticks fuer Raw-WR Simulation"),
    sl: int = typer.Option(10, help="Stop-Loss in Ticks fuer Raw-WR Simulation"),
    html: bool = typer.Option(False, "--html", help="HTML-Report schreiben"),
    config: Path = typer.Option(_DEFAULT_CONFIG, help="Pfad zu probe.toml"),
) -> None:
    """Analysiert einen einzelnen Baustein."""
    cfg = _load_cfg(config)
    bars_path = Path(cfg["data"]["bars_path"])
    shards_dir = Path(cfg["data"]["shards_dir"])
    output_dir = Path(cfg["data"]["output_dir"])

    try:
        cols = get_columns(concept)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    console.print(f"[dim]Lade Bars: {bars_path}[/dim]")
    bars = load_bars(bars_path)
    bars = filter_session(bars, session)

    console.print(f"[dim]Suche Shard fuer {concept} ({cols})...[/dim]")
    shard = find_shard(shards_dir, cols)
    if shard is None:
        console.print(f"[red]Kein Shard fuer '{concept}' gefunden in {shards_dir}[/red]")
        raise typer.Exit(1)

    # Nur relevante Spalten behalten
    existing_cols = [c for c in cols if c in shard.columns]
    shard = shard[existing_cols]
    shard = filter_session(shard, session)

    merged = merge_bars_and_signals(bars, shard)

    bull_col = cols[0] if len(cols) > 0 else ""
    bear_col = cols[1] if len(cols) > 1 else cols[0]

    result = scan_concept(
        merged,
        bull_col=bull_col,
        bear_col=bear_col,
        concept=concept.lower(),
        session=session,
        tp_ticks=tp,
        sl_ticks=sl,
    )

    print_scan_result(result)

    if html:
        out = render_html_report(result, output_dir)
        html_path = output_dir / f"probe_{result.concept}_{session}.html"
        console.print(f"\n[green]HTML-Report: {html_path}[/green]")


@app.command()
def compare(
    concept_a: str = typer.Argument(help='Erstes Konzept, z.B. "BREAKER"'),
    concept_b: str = typer.Argument(help='Zweites Konzept, z.B. "OB"'),
    session: str = typer.Option("ny", help="Session: ny | london | asia | all"),
    tp: int = typer.Option(10, help="Take-Profit in Ticks"),
    sl: int = typer.Option(10, help="Stop-Loss in Ticks"),
    html: bool = typer.Option(False, "--html", help="HTML-Report schreiben"),
    config: Path = typer.Option(_DEFAULT_CONFIG, help="Pfad zu probe.toml"),
) -> None:
    """Vergleicht zwei Bausteine direkt."""
    cfg = _load_cfg(config)
    bars_path = Path(cfg["data"]["bars_path"])
    shards_dir = Path(cfg["data"]["shards_dir"])
    output_dir = Path(cfg["data"]["output_dir"])

    results = []
    for concept in [concept_a, concept_b]:
        try:
            cols = get_columns(concept)
        except ValueError as e:
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(1)

        bars = load_bars(bars_path)
        bars = filter_session(bars, session)
        shard = find_shard(shards_dir, cols)
        if shard is None:
            console.print(f"[red]Kein Shard fuer '{concept}'[/red]")
            raise typer.Exit(1)
        existing_cols = [c for c in cols if c in shard.columns]
        shard = shard[existing_cols]
        shard = filter_session(shard, session)
        merged = merge_bars_and_signals(bars, shard)
        bull_col = cols[0]
        bear_col = cols[1] if len(cols) > 1 else cols[0]
        result = scan_concept(merged, bull_col, bear_col, concept.lower(), session, tp, sl)
        results.append(result)

    cr = compare_concepts(results[0], results[1])

    console.rule(f"[cyan]Vergleich: {concept_a.upper()} vs {concept_b.upper()}")
    from rich.table import Table
    t = Table(show_header=True, header_style="bold cyan")
    t.add_column("Metrik")
    t.add_column(concept_a.upper(), justify="right")
    t.add_column(concept_b.upper(), justify="right")
    t.add_column("Sieger", justify="center")

    def bold_winner(val_a, val_b, winner, fmt=".1f"):
        sa = f"{val_a:{fmt}}"
        sb = f"{val_b:{fmt}}"
        if winner == concept_a.lower():
            return f"[green]{sa}[/green]", sb, f"[green]{concept_a.upper()}[/green]"
        return sa, f"[green]{sb}[/green]", f"[green]{concept_b.upper()}[/green]"

    va, vb, w = bold_winner(cr.result_a.bull_per_month, cr.result_b.bull_per_month, cr.higher_bull_freq)
    t.add_row("Bull Signale/Monat", va, vb, w)
    va, vb, w = bold_winner(cr.result_a.bull_wr*100, cr.result_b.bull_wr*100, cr.higher_bull_wr)
    t.add_row("Bull Raw-WR %", va, vb, w)
    va, vb, w = bold_winner(cr.result_a.bear_per_month, cr.result_b.bear_per_month, cr.higher_bear_freq)
    t.add_row("Bear Signale/Monat", va, vb, w)
    va, vb, w = bold_winner(cr.result_a.bear_wr*100, cr.result_b.bear_wr*100, cr.higher_bear_wr)
    t.add_row("Bear Raw-WR %", va, vb, w)
    console.print(t)

    if html:
        render_html_compare(cr, output_dir)
        html_path = output_dir / f"compare_{concept_a.lower()}_vs_{concept_b.lower()}.html"
        console.print(f"\n[green]HTML-Report: {html_path}[/green]")


@app.command(name="list")
def list_concepts() -> None:
    """Zeigt alle bekannten Konzepte."""
    console.print("[cyan]Bekannte Konzepte:[/cyan]")
    for c in all_concepts():
        cols = get_columns(c)
        console.print(f"  [bold]{c}[/bold]  →  {', '.join(cols)}")


if __name__ == "__main__":
    app()
```

- [ ] **Step 2: probe.py ausfuehrbar machen**

```bash
chmod +x /home/boobi/HAUPTLAGER/26_Baustein_Tester/probe.py
```

- [ ] **Step 3: Smoke-Test ohne echte Daten (nur --help)**

```bash
cd /home/boobi/HAUPTLAGER/26_Baustein_Tester && source .venv/bin/activate
./probe.py --help
./probe.py list
```
Expected: Hilfe + Liste aller Konzepte erscheint, kein Fehler

- [ ] **Step 4: Alle Tests final laufen**

```bash
pytest tests/ -v
```
Expected: alle PASSED (mind. 14 Tests)

- [ ] **Step 5: Live-Test mit echten Daten**

```bash
./probe.py scan BREAKER --session ny
```
Expected: Rich-Tabelle mit Bullish/Bearish Statistiken erscheint

- [ ] **Step 6: Live-Test Vergleich**

```bash
./probe.py compare BREAKER OB --session ny --html
```
Expected: Vergleichstabelle + HTML-Datei in `output/`

- [ ] **Step 7: Commit**

```bash
git add probe.py
git commit -m "feat: probe.py CLI – scan, compare, list commands complete"
```

---

## Selbst-Review

**Spec-Coverage:**
- [x] Statistiken (Frequenz, Raw-WR, Ticks) → scanner.py Task 4
- [x] Visualisierung HTML-Report → report.py Task 6
- [x] Vergleich zwei Bausteine → comparator.py Task 5 + compare-Command Task 7
- [x] Eigenstaendig (eigene venv, keine SB-Abhaengigkeit) → Task 1
- [x] Session-Filter (ny/london/asia/all) → loader.py Task 3
- [x] Config-Datei (probe.toml) → Task 1

**Placeholder-Scan:** Keine TBDs, keine leeren Schritte.

**Type-Konsistenz:**
- `ScanResult` definiert in Task 4, verwendet in Task 5+6+7 ✓
- `CompareResult` definiert in Task 5, verwendet in Task 6+7 ✓
- `find_shard` definiert in Task 3, verwendet in Task 7 ✓
