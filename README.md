<p align="center">
  <h1 align="center">Baustein Tester</h1>
  <p align="center">
    <strong>Systematic scanner and comparator for trading signal building blocks.</strong>
  </p>
  <p align="center">
    <a href="#quick-start">Quick Start</a> · <a href="#scanning">Scanning</a> · <a href="#comparison">Comparison</a> · <a href="#output">Output</a>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/tests-4_suites_pass-brightgreen" alt="Tests passing">
  <img src="https://img.shields.io/badge/reporting-Rich_HTML-orange" alt="Rich HTML reports">
</p>

---

## Why?

When developing algorithmic trading strategies, you want to know *which signal concepts actually work*. Not in a full strategy, but as standalone building blocks.

**Baustein Tester isolates each concept** (FVG, Order Block, Liquidity Sweep, Breaker, etc.) and measures its statistical performance in isolation:

- **Hit rate** — does the signal predict direction?
- **Win rate** — if you trade the signal, what's your win rate?
- **Average move** — how far does price go after the signal?
- **Concept overlap** — which signals fire together?
- **Relative performance** — which concepts are stronger in which sessions/market regimes?

---

## Quick Start

```bash
pip install -r requirements.txt

# Scan a single concept
./probe.py scan BREAKER --session ny

# Compare two concepts
./probe.py compare BREAKER OB --session ny

# List all available concepts
./probe.py list

# Full scan + compare
./probe.py scan BREAKER --session ny --full
```

---

## Scanning

Scan a concept across your data to get per-bar signal statistics:

```bash
./probe.py scan BREAKER --session ny
```

```
Concept: BREAKER (ny session)
┌──────────┬──────────┬────────┬──────────┬──────────┐
│ Metric   │    Value │      % │    Count │   Total  │
├──────────┼──────────┼────────┼──────────┼──────────┤
│ Hit Rate │    0.532 │  53.2% │    1,247 │    2,344 │
│ Win Rate │    0.487 │  48.7% │      412 │      846 │
│ Avg Move │   +3.2pt │        │          │          │
│ Avg Gain │   +8.1pt │        │          │          │
│ Avg Loss │   -4.9pt │        │          │          │
│ Signals  │    2,344 │        │          │          │
└──────────┴──────────┴────────┴──────────┴──────────┘
```

### Available concepts

| Concept | Description |
|---------|-------------|
| `BREAKER` | Breaker block — failure of order block |
| `OB` | Order Block — institutional order flow |
| `FVG` | Fair Value Gap — price inefficiency |
| `Sweep` | Liquidity sweep — stop hunt |
| `BOS` | Break of Structure |
| `MSS` | Market Structure Shift |
| `iFVG` | Inverse Fair Value Gap |
| `PD_Array` | Premium/Discount Array |
| `SMT` | Smart Money Technique divergence |

---

## Comparison

Compare two or more concepts side-by-side:

```bash
./probe.py compare BREAKER OB --session ny
```

```
Comparing BREAKER vs OB (ny session)
┌──────────┬──────────┬──────────┬──────────┐
│ Metric   │  BREAKER │       OB │    Delta │
├──────────┼──────────┼──────────┼──────────┤
│ Hit Rate │   0.532  │   0.487  │  +0.045  │
│ Win Rate │   0.487  │   0.512  │  -0.025  │
│ Signals  │   2,344  │   1,892  │  +452    │
│ Overlap  │          │  42.3%   │          │
└──────────┴──────────┴──────────┴──────────┘
```

The comparison tells you:
- **Which concept has higher hit rate** — more predictive power
- **How much they overlap** — if they fire 80% together, they're redundant
- **Session bias** — some concepts work better in NY, London, or Asia

---

## Output

Results can be exported to HTML for easy sharing:

```bash
./probe.py scan BREAKER --full --html
```

Creates `output/compare_BREAKER_vs_OB.html` with interactive Rich tables.

---

## Project Structure

```
.
├── probe.py            # CLI entrypoint
├── probe.toml          # Data paths and configuration
├── bt/
│   ├── __init__.py
│   ├── concepts.py     # Signal concept registry
│   ├── loader.py       # Data loading with caching
│   ├── scanner.py      # Concept scanning engine
│   ├── comparator.py   # Concept comparison engine
│   └── report.py       # HTML report generation
├── tests/
│   ├── test_loader.py
│   ├── test_scanner.py
│   ├── test_comparator.py
│   └── test_report.py
└── requirements.txt
```

---

## Configuration

Edit `probe.toml`:

```toml
[data]
bars_path = "data/nq_1m_walkforward.parquet"  # 1-min NQ bars with signals
shards_dir = "data/signal_shards"               # Pre-computed signal columns
output_dir = "output"                           # HTML report output

[scan]
sessions = ["ny", "london", "asia"]
timeframes = ["1m", "5m", "15m"]
```

---

## Testing

```bash
pytest tests/ -v
```

All 4 test suites pass.

---

## License

MIT

<p align="center">
  <small>Built for systematic NQ futures research.<br>
  <strong>github.com/nessos666</strong></small>
</p>
