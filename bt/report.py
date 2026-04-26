from __future__ import annotations
from pathlib import Path
from rich.console import Console
from rich.table import Table
from bt.comparator import CompareResult
from bt.scanner import ScanResult

console = Console()

_HTML_SINGLE = """<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"><title>Baustein-Tester: {concept}</title>
<style>
  body{{font-family:monospace;background:#111;color:#eee;padding:2rem}}
  h1{{color:#7ec8e3}} table{{border-collapse:collapse;width:100%;margin:1rem 0}}
  th{{background:#222;color:#7ec8e3;padding:8px 12px;text-align:left}}
  td{{padding:6px 12px;border-bottom:1px solid #333}}
  .win{{color:#6fcf97}} .loss{{color:#eb5757}} .neutral{{color:#f2c94c}}
</style></head>
<body>
<h1>Baustein-Tester: {concept}</h1>
<p>Session: <b>{session}</b> | {date_from} → {date_to} | Bars: {total_bars:,}</p>
<h2>Bullish</h2>
<table>
<tr><th>Metrik</th><th>Wert</th></tr>
<tr><td>Signale gesamt</td><td>{bull_count:,}</td></tr>
<tr><td>Signale/Monat</td><td>{bull_per_month:.1f}</td></tr>
<tr><td>Raw Win-Rate (1:1)</td><td class="{bull_wr_class}">{bull_wr_pct:.1f}%</td></tr>
<tr><td>Ø Ticks bis TP</td><td>{avg_tp_ticks:.1f}</td></tr>
<tr><td>Ø Ticks bis SL</td><td>{avg_sl_ticks:.1f}</td></tr>
</table>
<h2>Bearish</h2>
<table>
<tr><th>Metrik</th><th>Wert</th></tr>
<tr><td>Signale gesamt</td><td>{bear_count:,}</td></tr>
<tr><td>Signale/Monat</td><td>{bear_per_month:.1f}</td></tr>
<tr><td>Raw Win-Rate (1:1)</td><td class="{bear_wr_class}">{bear_wr_pct:.1f}%</td></tr>
</table>
</body></html>"""

_HTML_COMPARE = """<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"><title>Vergleich: {concept_a} vs {concept_b}</title>
<style>
  body{{font-family:monospace;background:#111;color:#eee;padding:2rem}}
  h1{{color:#7ec8e3}} table{{border-collapse:collapse;width:100%;margin:1rem 0}}
  th{{background:#222;color:#7ec8e3;padding:8px 12px;text-align:left}}
  td{{padding:6px 12px;border-bottom:1px solid #333}}
  .winner{{color:#6fcf97;font-weight:bold}}
</style></head>
<body>
<h1>Vergleich: {concept_a} vs {concept_b}</h1>
<table>
<tr><th>Metrik</th><th>{concept_a}</th><th>{concept_b}</th><th>Sieger</th></tr>
<tr><td>Bull/Monat</td><td>{a_bull_freq:.1f}</td><td>{b_bull_freq:.1f}</td><td class="winner">{higher_bull_freq}</td></tr>
<tr><td>Bull WR</td><td>{a_bull_wr:.1f}%</td><td>{b_bull_wr:.1f}%</td><td class="winner">{higher_bull_wr}</td></tr>
<tr><td>Bear/Monat</td><td>{a_bear_freq:.1f}</td><td>{b_bear_freq:.1f}</td><td class="winner">{higher_bear_freq}</td></tr>
<tr><td>Bear WR</td><td>{a_bear_wr:.1f}%</td><td>{b_bear_wr:.1f}%</td><td class="winner">{higher_bear_wr}</td></tr>
</table>
</body></html>"""


def _wr_class(wr: float) -> str:
    if wr >= 0.52:
        return "win"
    if wr <= 0.45:
        return "loss"
    return "neutral"


def print_scan_result(result: ScanResult) -> None:
    console.rule(
        f"[cyan]Baustein: {result.concept.upper()} | Session: {result.session}"
    )
    console.print(
        f"Zeitraum: {result.date_from} → {result.date_to} | Bars: {result.total_bars:,}\n"
    )
    t = Table(show_header=True, header_style="bold cyan")
    t.add_column("Metrik")
    t.add_column("Bullish", justify="right")
    t.add_column("Bearish", justify="right")

    def wr_fmt(v: float) -> str:
        pct = f"{v * 100:.1f}%"
        if v >= 0.52:
            return f"[green]{pct}[/green]"
        if v <= 0.45:
            return f"[red]{pct}[/red]"
        return f"[yellow]{pct}[/yellow]"

    t.add_row("Signale gesamt", f"{result.bull_count:,}", f"{result.bear_count:,}")
    t.add_row(
        "Signale/Monat", f"{result.bull_per_month:.1f}", f"{result.bear_per_month:.1f}"
    )
    t.add_row("Raw Win-Rate (1:1)", wr_fmt(result.bull_wr), wr_fmt(result.bear_wr))
    t.add_row("Ø Ticks bis TP", f"{result.avg_tp_ticks:.1f}", "—")
    t.add_row("Ø Ticks bis SL", f"{result.avg_sl_ticks:.1f}", "—")
    console.print(t)


def render_html_report(result: ScanResult, output_dir: Path) -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    html = _HTML_SINGLE.format(
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
    out = Path(output_dir) / f"probe_{result.concept}_{result.session}.html"
    out.write_text(html, encoding="utf-8")
    return html


def render_html_compare(cr: CompareResult, output_dir: Path) -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    a, b = cr.result_a, cr.result_b
    html = _HTML_COMPARE.format(
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
    out = Path(output_dir) / f"compare_{a.concept}_vs_{b.concept}.html"
    out.write_text(html, encoding="utf-8")
    return html
