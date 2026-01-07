import pandas as pd
import matplotlib.pyplot as plt

res = pd.read_csv("spy_box_arbitrage_allpairs.csv", parse_dates=["date","expiration"])

daily = (res.assign(best=res[["profit_buy","profit_sell"]].max(axis=1))
           .groupby("date")["best"].max()
           .sort_index())

plt.figure()
daily.plot()
plt.title("Daily max box-arbitrage candidate profit (SPY)")
plt.ylabel("max profit (per share)")
plt.show()

covid = daily.loc["2020-02-15":"2020-04-30"]
plt.figure()
covid.plot()
plt.title("COVID window: daily max candidate profit (SPY)")
plt.ylabel("max profit (per share)")
plt.show()



plt.figure()
res["profit_sell"].hist(bins=60)
plt.title("Distribution of profit_sell (all pairs)")
plt.show()

plt.figure()
res.loc[(res["date"]>="2020-02-15") & (res["date"]<="2020-04-30"), "profit_sell"].hist(bins=60)
plt.title("Distribution of profit_sell (COVID window)")
plt.show()


res = pd.read_csv("spy_box_arbitrage_allpairs.csv", parse_dates=["date","expiration"])

plt.figure()
res["profit_buy"].hist(bins=60)
plt.title("Distribution of profit_buy (candidates rows)")
plt.show()

daily_min_buy = res.groupby("date")["profit_buy"].min().sort_index()
plt.figure()
daily_min_buy.plot()
plt.title("Daily min profit_buy (candidates rows)")
plt.show()