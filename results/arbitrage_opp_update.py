import numpy as np
import pandas as pd

# ----------------------------
# CONFIG
# ----------------------------
PATH = "./options/spy_option_chain.csv"  # same path style you used
OUT_ALL = "spy_box_arbitrage_allpairs.csv"
OUT_ADJ = "spy_box_arbitrage_adjacent.csv"

# arbitrage thresholds (in option price units, e.g. dollars per share)
MIN_PROFIT = 0.25      # ignore tiny "profits" that are likely noise/fees
MAX_SPREAD_PCT = 0.25  # drop strikes with very wide spreads (25%)
R = 0.00               # risk-free rate for discounting (keep 0 if you don't want to bother)

# COVID window (approx: vol spike / lockdown onset)
COVID_START = "2020-02-15"
COVID_END   = "2020-04-30"

# safety to avoid O(n^2) blow-ups on huge chains
MAX_STRIKES_PER_EXP = 250   # if more, keep the most liquid/tight-spread strikes only

# ----------------------------
# LOAD + CLEAN
# ----------------------------
df = pd.read_csv(PATH, parse_dates=["date", "expiration"])
df["strike"] = pd.to_numeric(df["strike"], errors="coerce")
df["bid"] = pd.to_numeric(df["bid"], errors="coerce")
df["ask"] = pd.to_numeric(df["ask"], errors="coerce")

df = df[["date", "act_symbol", "expiration", "strike", "call_put", "bid", "ask"]].dropna()

# basic quote sanity
df = df[(df["bid"] >= 0) & (df["ask"] >= df["bid"])]

# conservative aggregation for duplicate quotes:
# - best executable bid = max bid
# - best executable ask = min ask
agg = (
    df.groupby(["date", "act_symbol", "expiration", "strike", "call_put"], as_index=False)
      .agg(bid=("bid", "max"), ask=("ask", "min"))
)

# pivot to get Call_bid/ask and Put_bid/ask on one row
p = agg.pivot_table(
    index=["date", "act_symbol", "expiration", "strike"],
    columns="call_put",
    values=["bid", "ask"],
    aggfunc="first"
).dropna()

p.columns = [f"{cp}_{ba}" for ba, cp in p.columns]  # Call_bid, Call_ask, Put_bid, Put_ask
p = p.reset_index()

# spread filter to kill most fake "arb"
p["Call_spread_pct"] = (p["Call_ask"] - p["Call_bid"]) / np.maximum(p["Call_ask"], 1e-9)
p["Put_spread_pct"]  = (p["Put_ask"]  - p["Put_bid"])  / np.maximum(p["Put_ask"],  1e-9)

p = p[
    (p["Call_bid"] > 0) & (p["Put_bid"] > 0) &
    (p["Call_spread_pct"] <= MAX_SPREAD_PCT) &
    (p["Put_spread_pct"]  <= MAX_SPREAD_PCT)
].copy()

# ----------------------------
# BOX-SPREAD SCAN (adjacent + all-pairs)
# Long box cost:  +C(K1) -C(K2) -P(K1) +P(K2)
# Use ask for buys, bid for sells.
# cost_buy        = C1_ask - C2_bid + P2_ask - P1_bid
# Short box proceeds is the opposite using bid/ask.
# ----------------------------
def scan_boxes(group: pd.DataFrame, mode: str):
    g = group.sort_values("strike").set_index("strike")
    strikes = g.index.to_numpy()

    # downselect if too many strikes
    if len(strikes) > MAX_STRIKES_PER_EXP:
        tmp = group.copy()
        tmp["spread_score"] = tmp["Call_spread_pct"] + tmp["Put_spread_pct"]
        tmp = tmp.sort_values(["spread_score"]).head(MAX_STRIKES_PER_EXP)
        g = tmp.sort_values("strike").set_index("strike")
        strikes = g.index.to_numpy()

    if len(strikes) < 2:
        return []

    # time to expiry discount
    d = group["date"].iloc[0]
    exp = group["expiration"].iloc[0]
    T = max((exp - d).days / 365.0, 0.0)
    disc = np.exp(-R * T)

    out = []

    if mode == "adjacent":
        for i in range(len(strikes) - 1):
            K1, K2 = float(strikes[i]), float(strikes[i + 1])

            C1a, C1b = float(g.loc[K1, "Call_ask"]), float(g.loc[K1, "Call_bid"])
            P1a, P1b = float(g.loc[K1, "Put_ask"]),  float(g.loc[K1, "Put_bid"])
            C2a, C2b = float(g.loc[K2, "Call_ask"]), float(g.loc[K2, "Call_bid"])
            P2a, P2b = float(g.loc[K2, "Put_ask"]),  float(g.loc[K2, "Put_bid"])

            payoff_pv = (K2 - K1) * disc

            cost_buy = C1a - C2b + P2a - P1b
            profit_buy = payoff_pv - cost_buy

            proceeds_sell = C1b - C2a + P2b - P1a
            profit_sell = proceeds_sell - payoff_pv

            if (profit_buy >= MIN_PROFIT) or (profit_sell >= MIN_PROFIT):
                out.append([d, group["act_symbol"].iloc[0], exp, K1, K2, payoff_pv,
                            cost_buy, profit_buy, proceeds_sell, profit_sell, T])

        return out

    # all pairs (O(n^2))
    for i in range(len(strikes) - 1):
        K1 = float(strikes[i])
        C1a, C1b = float(g.loc[K1, "Call_ask"]), float(g.loc[K1, "Call_bid"])
        P1a, P1b = float(g.loc[K1, "Put_ask"]),  float(g.loc[K1, "Put_bid"])

        for j in range(i + 1, len(strikes)):
            K2 = float(strikes[j])
            C2a, C2b = float(g.loc[K2, "Call_ask"]), float(g.loc[K2, "Call_bid"])
            P2a, P2b = float(g.loc[K2, "Put_ask"]),  float(g.loc[K2, "Put_bid"])

            payoff_pv = (K2 - K1) * disc

            cost_buy = C1a - C2b + P2a - P1b
            profit_buy = payoff_pv - cost_buy

            proceeds_sell = C1b - C2a + P2b - P1a
            profit_sell = proceeds_sell - payoff_pv

            if (profit_buy >= MIN_PROFIT) or (profit_sell >= MIN_PROFIT):
                out.append([d, group["act_symbol"].iloc[0], exp, K1, K2, payoff_pv,
                            cost_buy, profit_buy, proceeds_sell, profit_sell, T])

    return out


def run(mode: str, out_path: str):
    rows = []
    for _, grp in p.groupby(["date", "act_symbol", "expiration"], sort=False):
        rows.extend(scan_boxes(grp, mode=mode))

    res = pd.DataFrame(rows, columns=[
        "date","act_symbol","expiration","K1","K2","payoff_pv",
        "cost_buy","profit_buy","proceeds_sell","profit_sell","T_years"
    ])

    if res.empty:
        print(f"[{mode}] No candidates found after filters.")
        return res

    res.to_csv(out_path, index=False)

    # overall top candidates
    print(f"\n[{mode}] TOP SELL-BOX (candidates):")
    print(res.sort_values("profit_sell", ascending=False).head(15).to_string(index=False))

    print(f"\n[{mode}] TOP BUY-BOX (candidates):")
    print(res.sort_values("profit_buy", ascending=False).head(15).to_string(index=False))

    # covid focus
    covid = res[(res["date"] >= COVID_START) & (res["date"] <= COVID_END)]
    print(f"\n[{mode}] COVID WINDOW {COVID_START} -> {COVID_END}")
    if covid.empty:
        print("No candidates in COVID window after filters.")
    else:
        print("\nTop SELL-BOX during COVID:")
        print(covid.sort_values("profit_sell", ascending=False).head(15).to_string(index=False))
        print("\nTop BUY-BOX during COVID:")
        print(covid.sort_values("profit_buy", ascending=False).head(15).to_string(index=False))

        # simple daily summary
        daily = (covid.assign(best_profit=covid[["profit_buy","profit_sell"]].max(axis=1))
                      .groupby("date")
                      .agg(n_candidates=("best_profit","size"),
                           max_profit=("best_profit","max"))
                      .sort_values("max_profit", ascending=False)
                )
        print("\nDaily summary (COVID):")
        print(daily.head(20).to_string())

    return res


# run both modes
res_all = run(mode="allpairs", out_path=OUT_ALL)
res_adj = run(mode="adjacent", out_path=OUT_ADJ)
