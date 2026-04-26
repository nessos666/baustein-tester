from __future__ import annotations

import tomllib
from pathlib import Path

import pandas as pd

# UTC-Stunden fuer Session-Filter (start_inclusive, end_exclusive)
_SESSION_UTC: dict[str, tuple[float, float]] = {
    "london": (7.0, 11.0),
    "ny": (13.5, 16.0),
    "asia": (1.0, 4.0),
}


def load_config(config_path: Path = Path("probe.toml")) -> dict:
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def _normalize_index_to_utc(df: pd.DataFrame) -> pd.DataFrame:
    """Konvertiert Index auf UTC – vermeidet System-pytz/zoneinfo Abhaengigkeit."""
    if not isinstance(df.index, pd.DatetimeIndex):
        return df
    df.index = pd.to_datetime(df.index, utc=True)
    return df


def load_bars(bars_path: Path) -> pd.DataFrame:
    """Laedt NQ-1m-Bars aus Parquet. Index muss DatetimeIndex sein."""
    df = pd.read_parquet(bars_path)
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError(f"Bars-Index ist kein DatetimeIndex: {type(df.index)}")
    df.columns = [c.lower() for c in df.columns]
    return _normalize_index_to_utc(df)


def load_shard(shard_path: Path) -> pd.DataFrame:
    """Laedt einen Signal-Shard aus Parquet."""
    df = pd.read_parquet(shard_path)
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError(f"Shard-Index ist kein DatetimeIndex: {type(df.index)}")
    return _normalize_index_to_utc(df)


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
    decimal_hours = idx_utc.hour + idx_utc.minute / 60.0
    mask = (decimal_hours >= start_h) & (decimal_hours < end_h)
    return df[mask]


def merge_bars_and_signals(bars: pd.DataFrame, signals: pd.DataFrame) -> pd.DataFrame:
    """Joined Bars und Signals auf gemeinsamem Index (inner join)."""
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
    for col in sigs_utc.columns:
        if col in merged.columns:
            merged[col] = merged[col].fillna(False).astype(bool)
    return merged
