#!/usr/bin/env python3
"""Baustein-Tester – analysiert einzelne PDA-Bausteine.

Verwendung:
  ./probe.py scan BREAKER --session ny
  ./probe.py compare BREAKER OB --session ny
  ./probe.py list
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from bt.comparator import compare_concepts
from bt.concepts import all_concepts, get_columns
from bt.loader import (
    filter_session,
    find_shard,
    load_bars,
    load_config,
    merge_bars_and_signals,
)
from bt.report import print_scan_result, render_html_compare, render_html_report
from bt.scanner import scan_concept

app = typer.Typer(help="Baustein-Tester – PDA-Bausteine statistisch analysieren.")
console = Console()

_DEFAULT_CONFIG = Path(__file__).parent / "probe.toml"


def _load_cfg(config: Path) -> dict:
    try:
        return load_config(config)
    except FileNotFoundError:
        console.print(f"[red]Config nicht gefunden: {config}[/red]")
        raise typer.Exit(1)


def _scan_one(concept: str, session: str, tp: int, sl: int, cfg: dict):
    """Hilfsfunktion: einen Baustein laden und scannen."""
    bars_path = Path(cfg["data"]["bars_path"])
    shards_dir = Path(cfg["data"]["shards_dir"])

    cols = get_columns(concept)
    bars = load_bars(bars_path)
    bars = filter_session(bars, session)

    shard = find_shard(shards_dir, cols)
    if shard is None:
        console.print(f"[red]Kein Shard fuer '{concept}' in {shards_dir}[/red]")
        raise typer.Exit(1)

    existing_cols = [c for c in cols if c in shard.columns]
    shard = shard[existing_cols]
    shard = filter_session(shard, session)
    merged = merge_bars_and_signals(bars, shard)

    bull_col = cols[0]
    bear_col = cols[1] if len(cols) > 1 else cols[0]

    return scan_concept(merged, bull_col, bear_col, concept.lower(), session, tp, sl)


@app.command()
def scan(
    concept: str = typer.Argument(help='Konzept-Name, z.B. "BREAKER" oder "BB"'),
    session: str = typer.Option("ny", help="Session: ny | london | asia | all"),
    tp: int = typer.Option(10, help="Take-Profit in Ticks"),
    sl: int = typer.Option(10, help="Stop-Loss in Ticks"),
    html: bool = typer.Option(False, "--html", help="HTML-Report schreiben"),
    config: Path = typer.Option(_DEFAULT_CONFIG, help="Pfad zu probe.toml"),
) -> None:
    """Analysiert einen einzelnen Baustein."""
    cfg = _load_cfg(config)
    try:
        get_columns(concept)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    console.print(
        f"[dim]Lade Daten fuer {concept.upper()} | Session: {session}...[/dim]"
    )
    result = _scan_one(concept, session, tp, sl, cfg)
    print_scan_result(result)

    if html:
        output_dir = Path(cfg["data"]["output_dir"])
        render_html_report(result, output_dir)
        console.print(
            f"[green]HTML: {output_dir}/probe_{result.concept}_{session}.html[/green]"
        )


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
    """Vergleicht zwei Bausteine."""
    cfg = _load_cfg(config)
    for c in [concept_a, concept_b]:
        try:
            get_columns(c)
        except ValueError as e:
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(1)

    console.print(f"[dim]Scanne {concept_a.upper()} und {concept_b.upper()}...[/dim]")
    result_a = _scan_one(concept_a, session, tp, sl, cfg)
    result_b = _scan_one(concept_b, session, tp, sl, cfg)
    cr = compare_concepts(result_a, result_b)

    console.rule(f"[cyan]Vergleich: {concept_a.upper()} vs {concept_b.upper()}")
    t = Table(show_header=True, header_style="bold cyan")
    t.add_column("Metrik")
    t.add_column(concept_a.upper(), justify="right")
    t.add_column(concept_b.upper(), justify="right")
    t.add_column("Sieger", justify="center")

    def row(label, va, vb, winner, fmt=".1f"):
        sa, sb = f"{va:{fmt}}", f"{vb:{fmt}}"
        if winner == concept_a.lower():
            return (
                label,
                f"[green]{sa}[/green]",
                sb,
                f"[green]{concept_a.upper()}[/green]",
            )
        return label, sa, f"[green]{sb}[/green]", f"[green]{concept_b.upper()}[/green]"

    t.add_row(
        *row(
            "Bull/Monat",
            result_a.bull_per_month,
            result_b.bull_per_month,
            cr.higher_bull_freq,
        )
    )
    t.add_row(
        *row(
            "Bull WR %",
            result_a.bull_wr * 100,
            result_b.bull_wr * 100,
            cr.higher_bull_wr,
        )
    )
    t.add_row(
        *row(
            "Bear/Monat",
            result_a.bear_per_month,
            result_b.bear_per_month,
            cr.higher_bear_freq,
        )
    )
    t.add_row(
        *row(
            "Bear WR %",
            result_a.bear_wr * 100,
            result_b.bear_wr * 100,
            cr.higher_bear_wr,
        )
    )
    console.print(t)

    if html:
        output_dir = Path(cfg["data"]["output_dir"])
        render_html_compare(cr, output_dir)
        console.print(
            f"[green]HTML: {output_dir}/compare_{concept_a.lower()}_vs_{concept_b.lower()}.html[/green]"
        )


@app.command(name="list")
def list_concepts() -> None:
    """Zeigt alle bekannten Konzepte."""
    console.print("[cyan]Bekannte Konzepte:[/cyan]")
    for c in all_concepts():
        cols = get_columns(c)
        console.print(f"  [bold]{c}[/bold]  →  {', '.join(cols)}")


if __name__ == "__main__":
    app()
