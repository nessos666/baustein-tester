<p align="center">
  <h1 align="center">Baustein Tester</h1>
  <p align="center">
    <strong>Systematic scanner and comparator for trading signal building blocks — find out which concepts actually work before you build a strategy around them.</strong>
  </p>
  <p align="center">
    <a href="#why">Why</a> · <a href="#workflow">Workflow</a> · <a href="#scanning">Scanning</a> · <a href="#comparison">Comparison</a> · <a href="#interpretation">Interpretation</a> · <a href="#output">Output</a>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/tests-4_suites_pass-brightgreen" alt="Tests passing">
  <img src="https://img.shields.io/badge/reporting-Rich_HTML-orange" alt="Rich HTML reports">
  <img src="https://img.shields.io/github/stars/nessos666/baustein-tester?style=social" alt="Stars">
</p>

---

## Why?

When developing algorithmic trading strategies, you face a fundamental problem: **you don't know which signal concepts actually work**.

Traditional approaches are flawed:

| Approach | Problem |
|----------|---------|
| **Full strategy backtest** | Can't isolate individual concepts — performance is confounded by entry logic, exit logic, filters |
| **Paper trading** | Takes weeks to get statistically significant sample sizes |
| **Intuition / "it feels right"** | Confirmation bias — you see what you want to see |
| **Academic papers** | Tested on different instruments, different time periods, different market regimes |

**Baustein Tester solves this.** It isolates each concept (FVG, Order Block, Liquidity Sweep, Breaker, etc.) and measures its standalone statistical performance across thousands of bars:

- **Hit rate** — what % of signals predict the correct direction?
- **Win rate** — if you traded every signal, what's your win rate?
- **Average move** — how far does price typically go after a signal?
- **Concept overlap** — which signals fire at the same time?
- **Session bias** — does a concept work better in NY, London, or Asia?
- **Regime sensitivity** — does performance change in bull vs bear markets?

---

## Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Baustein Tester Pipeline                        │
│                                                                     │
│  1. Load bars with pre-computed signal columns (parquet)            │
│  2. Filter by session / timeframe / market regime                   │
│  3. For each concept:                                               │
│     ┌──────────────────────────────────────────────────────┐       │
│     │  Scan: hit rate, win rate, avg move, avg gain/loss   │       │
│     └──────────────────────────────────────────────────────┘       │
│  4. Compare concepts: overlap matrix, win rate delta,              │
│     session breakdown                                              │
│  5. Export: terminal table (Rich) or interactive HTML report       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
pip install -r requirements.txt

# List all available concepts
./probe.py list

# Scan a single concept in NY session
./probe.py scan BREAKER --session ny

# Compare two concepts
./probe.py compare BREAKER OB --session ny

# Full scan with HTML report
./probe.py scan BREAKER --session ny --full --html
```

---

## Scanning

The scanner analyzes every occurrence of a concept across your data and computes **per-bar statistics**:

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

| Concept | Description | Category |
|---------|-------------|----------|
| `BREAKER` | Breaker block — failure of an order block | Reversal |
| `OB` | Order Block — institutional order flow origin | Continuation/Reversal |
| `FVG` | Fair Value Gap — price inefficiency | Imbalance |
| `Sweep` | Liquidity Sweep — stop hunt above/below structure | Trap |
| `BOS` | Break of Structure — confirmed trend shift | Momentum |
| `MSS` | Market Structure Shift — aggressive reversal | Reversal |
| `iFVG` | Inverse Fair Value Gap — refilled imbalance | Support/Resistance |
| `PD_Array` | Premium/Discount Array — Fibonacci-based zones | Context |
| `SMT` | Smart Money Technique — divergence between correlated assets | Divergence |

### Session filter

```bash
# Scan in London session
./probe.py scan FVG --session london

# Scan in Asia session
./probe.py scan SWEEP --session asia

# Scan across ALL sessions
./probe.py scan OB --full
```

---

## Comparison

The comparator puts concepts side-by-side to reveal which ones actually add value:

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

### Multi-concept comparison

```bash
# Compare three concepts at once
./probe.py compare FVG OB SWEEP --session ny

# Compare across sessions
./probe.py compare BREAKER OB --full
```

---

## Interpretation

Here's how to read the results and what to do with them:

### Hit rate > 50%

The concept predicts direction better than chance. This is the **first filter** — anything below 50% is probably noise.

### Win rate vs hit rate

- **Win rate ≈ hit rate** — the concept has symmetric risk/reward
- **Win rate > hit rate** — winners are bigger than losers, even if less frequent
- **Win rate < hit rate** — losers are bigger than winners (tight stops, wide targets)

### Overlap

If two concepts overlap 80%+, they're measuring the **same market structure** under different names. Don't combine them in a strategy — one is redundant.

### Session bias

| Pattern | What it means |
|---------|---------------|
| Higher in NY | The concept is driven by institutional order flow |
| Higher in London | The concept captures overnight positioning |
| Higher in Asia | The concept works in thin liquidity environments |
| No difference | The concept is market-structure agnostic |

---

## Example: Session Breakdown

```bash
./probe.py scan FVG --full
```

```
Concept: FVG
┌──────────┬──────────┬──────────┬──────────┐
│ Session  │ Hit Rate │ Win Rate │  Signals │
├──────────┼──────────┼──────────┼──────────┤
│ NY AM    │   0.548  │   0.512  │    1,234 │
│ London   │   0.512  │   0.478  │      892 │
│ Asia     │   0.489  │   0.501  │      445 │
│ PM       │   0.503  │   0.495  │      723 │
│ Pre      │   0.471  │   0.462  │      156 │
└──────────┴──────────┴──────────┴──────────┘
```

This tells you: **FVG works best in NY AM session** (54.8% hit rate) and is significantly worse in Asia (48.9%). If you're building a strategy around FVGs, the session filter is critical.

---

## Output

Results can be exported to HTML for sharing with teams or documentation:

```bash
./probe.py scan BREAKER --full --html
```

Creates `output/compare_BREAKER_vs_OB.html` with interactive Rich tables.

---

## Project Structure

```
.
├── probe.py            # CLI entrypoint (194 lines)
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
bars_path = "data/nq_1m_walkforward.parquet"
shards_dir = "data/signal_shards"
output_dir = "output"

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

## Related

Part of the NQ research ecosystem:

- [nq-strategy-builder](https://github.com/nessos666/nq-strategy-builder) — Build full strategies from these building blocks
- [quant-tools](https://github.com/nessos666/quant-tools) — Statistical tools for market data analysis
- [tv-watch-agent](https://github.com/nessos666/tv-watch-agent) — Automated TradingView chart surveillance

---

## License

MIT

<p align="center">
  <small>Built for systematic NQ futures research. Know your edge before you trade it.<br>
  <strong>github.com/nessos666</strong></small>
</p>
