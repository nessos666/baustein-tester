from __future__ import annotations

# Konzept-Name (lowercase) → Spalten im Signal-Shard
_CONCEPT_COLUMNS: dict[str, list[str]] = {
    "bos": ["bos_bullish", "bos_bearish"],
    "choch": ["choch_bullish", "choch_bearish"],
    "ob": ["ob_bullish", "ob_bearish"],
    "mb": ["mb_bullish", "mb_bearish"],
    "fvg": ["fvg_bullish", "fvg_bearish"],
    "ifvg": ["ifvg_bullish", "ifvg_bearish"],
    "bpr": ["bpr_bullish", "bpr_bearish"],
    "breaker": ["breaker_bullish", "breaker_bearish"],
    "rb": ["rb_bullish", "rb_bearish"],
    "sweep": ["swept_buy_side", "swept_sell_side"],
    "judas": ["js_bullish", "js_bearish"],
    "silver_bullet": ["sb_entry_long", "sb_entry_short"],
    "manip": ["manip_bullish", "manip_bearish"],
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
        raise ValueError(
            f"Unbekanntes Konzept: '{concept}'. Bekannt: {sorted(_CONCEPT_COLUMNS)}"
        )
    return _CONCEPT_COLUMNS[key]


def all_concepts() -> list[str]:
    """Liste aller bekannten Konzepte (ohne Aliase)."""
    return sorted(_CONCEPT_COLUMNS)
