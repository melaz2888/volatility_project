## volatility + options arbitrage scan (spy)

small python project using dolthub options data exported locally as csv.

## what this repo does

- volatility diagnostics on spy 
  - rolling realized volatility (annualized)
  - ewma realized volatility (riskmetrics-style)
  - optional plots vs vix
- option-chain scan (bid/ask) to compute box-spread metrics
  - cost_buy, profit_buy (long box)
  - proceeds_sell, profit_sell (short box)
- saves results to csv for later analysis

## data (dolthub + dolt sql)

source database: post-no-preference/options

tables used:
- option_chain
- volatility_history

clone:
dolt clone post-no-preference/options
cd options

export spy volatility history (csv):
dolt sql -r csv -q "SELECT date, act_symbol, iv_current, hv_current FROM volatility_history WHERE act_symbol = 'SPY' ORDER BY date;" > ../options/spy_volatility_history.csv

export spy option chain (csv):
dolt sql -r csv -q "SELECT date, act_symbol, expiration, strike, call_put, bid, ask FROM option_chain WHERE act_symbol = 'SPY' AND date >= '2019-01-01' AND date <= '2020-06-01' ORDER BY date, expiration, strike;" > ../options/spy_option_chain.csv

expected local paths:
- ./options/spy_option_chain.csv
- ./options/spy_volatility_history.csv

## setup

python -m venv .venv
# windows: .venv\Scripts\activate
# macos/linux: source .venv/bin/activate
pip install -r requirements.txt

## run

volatility:
python main.py

arbitrage scan:
python your_scan_script.py

outputs:
- spy_box_arbitrage_allpairs.csv
- spy_box_arbitrage_adjacent.csv
