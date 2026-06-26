# SIGNAL DECK NASDAQ

Real-time NQ/MNQ NASDAQ futures analysis engine for PAPER TRADING EDUCATION only.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the analysis engine via CLI:

```bash
python3 -m silver_deck.cli
```

## Prop-firm risk inputs

Defaults are tuned for a ₦200,000 demo prop-firm account with 20% max drawdown and a 10% phase target:

```bash
export ACCOUNT_BALANCE_NGN=200000
export MAX_DRAWDOWN_PCT=20
export PROFIT_TARGET_PCT=10
export PHASE_COUNT=2
export USD_NGN_RATE=1500  # optional; required to convert MNQ/NQ dollar risk into naira
```

If `USD_NGN_RATE` is not set, the engine shows naira drawdown and phase budgets but will not fabricate contract-risk conversion.

## Disclaimer

This is not financial advice. Never recommend real-money trading. For educational purposes only.
