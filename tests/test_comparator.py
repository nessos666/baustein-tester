from bt.comparator import compare_concepts, CompareResult
from bt.scanner import ScanResult


def _make_result(concept, bull_wr, bull_count):
    return ScanResult(
        concept=concept,
        session="ny",
        total_bars=10000,
        date_from="2024-01-01",
        date_to="2026-01-01",
        bull_count=bull_count,
        bull_per_month=bull_count / 24,
        bull_wr=bull_wr,
        avg_tp_ticks=10.0,
        avg_sl_ticks=10.0,
        bear_count=bull_count,
        bear_per_month=bull_count / 24,
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
