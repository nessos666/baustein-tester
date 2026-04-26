from __future__ import annotations

from dataclasses import dataclass

from bt.scanner import ScanResult


@dataclass
class CompareResult:
    result_a: ScanResult
    result_b: ScanResult
    higher_bull_wr: str
    higher_bear_wr: str
    higher_bull_freq: str
    higher_bear_freq: str


def compare_concepts(a: ScanResult, b: ScanResult) -> CompareResult:
    return CompareResult(
        result_a=a,
        result_b=b,
        higher_bull_wr=a.concept if a.bull_wr >= b.bull_wr else b.concept,
        higher_bear_wr=a.concept if a.bear_wr >= b.bear_wr else b.concept,
        higher_bull_freq=a.concept
        if a.bull_per_month >= b.bull_per_month
        else b.concept,
        higher_bear_freq=a.concept
        if a.bear_per_month >= b.bear_per_month
        else b.concept,
    )
