from bt.report import print_scan_result, render_html_report
from bt.scanner import ScanResult


def _make_result():
    return ScanResult(
        concept="breaker",
        session="ny",
        total_bars=699248,
        date_from="2024-03-25",
        date_to="2026-03-25",
        bull_count=423,
        bull_per_month=17.6,
        bull_wr=0.521,
        avg_tp_ticks=10.0,
        avg_sl_ticks=10.0,
        bear_count=424,
        bear_per_month=17.7,
        bear_wr=0.489,
    )


def test_print_scan_result_runs_without_error():
    # Rich schreibt in Terminal – nur sicherstellen kein Exception
    print_scan_result(_make_result())


def test_render_html_contains_concept_name(tmp_path):
    html = render_html_report(_make_result(), output_dir=tmp_path)
    assert "breaker" in html.lower()
    assert "52.1" in html or "521" in html


def test_render_html_writes_file(tmp_path):
    render_html_report(_make_result(), output_dir=tmp_path)
    files = list(tmp_path.glob("*.html"))
    assert len(files) == 1


def test_render_html_compare_contains_both(tmp_path):
    from bt.comparator import compare_concepts
    from bt.report import render_html_compare

    a = _make_result()
    b = ScanResult(
        concept="ob",
        session="ny",
        total_bars=699248,
        date_from="2024-03-25",
        date_to="2026-03-25",
        bull_count=300,
        bull_per_month=12.5,
        bull_wr=0.48,
        avg_tp_ticks=10.0,
        avg_sl_ticks=10.0,
        bear_count=310,
        bear_per_month=12.9,
        bear_wr=0.46,
    )
    cr = compare_concepts(a, b)
    html = render_html_compare(cr, output_dir=tmp_path)
    assert "breaker" in html.lower()
    assert "ob" in html.lower()
