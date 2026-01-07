import pandas as pd

df = pd.read_csv("./options/spy_option_chain.csv", parse_dates=["date", "expiration"])
df["strike"] = df["strike"].astype(float)

# keep only needed cols
df = df[["date","act_symbol","expiration","strike","call_put","bid","ask"]]

# pivot to get columns:
# Call_bid, Call_ask, Put_bid, Put_ask per (date, sym, exp, strike)
p = df.pivot_table(
    index=["date","act_symbol","expiration","strike"],  # we use this 
                                #to group the call put bid ask for the same strike price
    columns="call_put",
    values=["bid","ask"],
    aggfunc="first"
).dropna()

p.columns = [f"{cp}_{ba}" for ba, cp in p.columns]  # e.g. Call_bid
p = p.reset_index()

# print(p.head())
# scan each (date,sym,exp) across strike pairs
out = []
for (d,sym,exp), g in p.groupby(["date","act_symbol","expiration"]):
    g = g.sort_values("strike")
    strikes = g["strike"].to_list()
    g = g.set_index("strike")

    for i in range(len(strikes)-1):
        K1, K2 = strikes[i], strikes[i+1]   # start with adjacent strikes (simple)
        C1a = g.loc[K1, "Call_ask"]; C2b = g.loc[K2, "Call_bid"]
        P2a = g.loc[K2, "Put_ask"];  P1b = g.loc[K1, "Put_bid"]

        cost_buy = C1a - C2b + P2a - P1b
        payoff = K2 - K1
        profit_buy = payoff - cost_buy

        C1b = g.loc[K1, "Call_bid"]; C2a = g.loc[K2, "Call_ask"]
        P2b = g.loc[K2, "Put_bid"];  P1a = g.loc[K1, "Put_ask"]

        proceeds_sell = C1b - C2a + P2b - P1a
        profit_sell = proceeds_sell - payoff

        out.append([d,sym,exp,K1,K2,cost_buy,profit_buy,proceeds_sell,profit_sell])

res = pd.DataFrame(out, columns=[
    "date","act_symbol","expiration","K1","K2",
    "cost_buy","profit_buy","proceeds_sell","profit_sell"
])

res.to_csv("spy_arbitrage_opportunities.csv", index=False)
# # show best candidates
# print(res.sort_values("profit_buy", ascending=False).head(20))
# print(res.sort_values("profit_sell", ascending=False).head(20))
