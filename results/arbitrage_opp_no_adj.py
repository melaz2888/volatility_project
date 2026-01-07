import pandas as pd

# 1) load raw option chain
df = pd.read_csv("./options/spy_option_chain.csv", parse_dates=["date","expiration"])
df["strike"] = df["strike"].astype(float)

# keep only what we need
df = df[["date","act_symbol","expiration","strike","call_put","bid","ask"]]

# 2) pivot: one row per (date, symbol, exp, strike) with Call/Put bid/ask as columns
p = df.pivot_table(
    index=["date","act_symbol","expiration","strike"],
    columns="call_put",
    values=["bid","ask"],
    aggfunc="first"
).dropna()

p.columns = [f"{cp}_{ba}" for ba, cp in p.columns]  # -> Call_bid, Call_ask, Put_bid, Put_ask
p = p.reset_index()

# 3) scan ALL strike pairs K1 < K2 per (date,symbol,expiration)
out = []
for (d,sym,exp), g in p.groupby(["date","act_symbol","expiration"]):
    g = g.sort_values("strike").set_index("strike")
    strikes = g.index.to_list()
    if len(strikes) < 2:
        continue

    for i in range(len(strikes)):
        K1 = strikes[i]
        C1a, C1b = g.loc[K1, "Call_ask"], g.loc[K1, "Call_bid"]
        P1a, P1b = g.loc[K1, "Put_ask"],  g.loc[K1, "Put_bid"]

        for j in range(i+1, len(strikes)):
            K2 = strikes[j]
            C2a, C2b = g.loc[K2, "Call_ask"], g.loc[K2, "Call_bid"]
            P2a, P2b = g.loc[K2, "Put_ask"],  g.loc[K2, "Put_bid"]

            payoff = K2 - K1

            cost_buy = C1a - C2b + P2a - P1b
            profit_buy = payoff - cost_buy

            proceeds_sell = C1b - C2a + P2b - P1a
            profit_sell = proceeds_sell - payoff

            out.append([d,sym,exp,K1,K2,cost_buy,profit_buy,proceeds_sell,profit_sell])

res = pd.DataFrame(out, columns=[
    "date","act_symbol","expiration","K1","K2",
    "cost_buy","profit_buy","proceeds_sell","profit_sell"
])

# 4) show top results
print("TOP BUY-BOX:")
print(res.sort_values("profit_buy", ascending=False).head(20).to_string(index=False))

print("\nTOP SELL-BOX:")
print(res.sort_values("profit_sell", ascending=False).head(20).to_string(index=False))

# 5) save if you want
res.to_csv("spy_arbitrage_opportunities_allpairs.csv", index=False)
