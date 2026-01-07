# Volatility Project

A small Python project to fetch historical prices with `yfinance` and compute volatility measures:
- Rolling (annualized) volatility over configurable windows
- EWMA (RiskMetrics-style) volatility
- Simple event impact analysis (pre/post volatility)
- Plot comparison

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Notes
- Uses log returns from adjusted close (fallbacks to close).
- Annualization assumes 252 trading days.
