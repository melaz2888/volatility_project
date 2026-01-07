import pandas as pd

df = pd.read_csv("spy_arbitrage_opportunities.csv", parse_dates=["date","expiration"])

# keep only meaningful positives (tune threshold if needed)
df_buy  = df[df["profit_buy"]  > 0.05].sort_values("profit_buy", ascending=False)
df_sell = df[df["profit_sell"] > 0.05].sort_values("profit_sell", ascending=False)

print("TOP BUY-BOX opportunities:")
print(df_buy[["date","expiration","K1","K2","cost_buy","profit_buy"]].head(20).to_string(index=False))

print("\nTOP SELL-BOX opportunities:")
print(df_sell[["date","expiration","K1","K2","proceeds_sell","profit_sell"]].head(20).to_string(index=False))
