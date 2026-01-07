import pandas as pd
import matplotlib.pyplot as plt

res = pd.read_csv("spy_box_arbitrage_allpairs.csv", parse_dates=["date","expiration"])

print("profit_sell min/max:", res["profit_sell"].min(), res["profit_sell"].max())
print("profit_buy  min/max:", res["profit_buy"].min(),  res["profit_buy"].max())

g = res.groupby("date")

ts = pd.DataFrame({
    "sell_max": g["profit_sell"].max(),
    "sell_med": g["profit_sell"].median(),
    "sell_min": g["profit_sell"].min(),
    "buy_max":  g["profit_buy"].max(),
    "buy_med":  g["profit_buy"].median(),
    "buy_min":  g["profit_buy"].min(),
}).sort_index()

plt.figure()
ts[["sell_max","sell_med","sell_min"]].plot()
plt.title("profit_sell time series (dataset)")
plt.ylabel("profit per share")
plt.show()

plt.figure()
ts[["buy_max","buy_med","buy_min"]].plot()
plt.title("profit_buy time series (dataset)")
plt.ylabel("profit per share")
plt.show()



import pandas as pd
import matplotlib.pyplot as plt

res = pd.read_csv("spy_box_arbitrage_allpairs.csv", parse_dates=["date","expiration"])
res = res.sort_values("date")

plt.figure()
plt.scatter(res["date"], res["profit_sell"], s=6)
plt.title("profit_sell over time (all rows)")
plt.ylabel("profit per share")
plt.xlabel("date")
plt.show()

plt.figure()
plt.scatter(res["date"], res["profit_buy"], s=6)
plt.title("profit_buy over time (all rows)")
plt.ylabel("profit per share")
plt.xlabel("date")
plt.show()


import pandas as pd
import matplotlib.pyplot as plt

res = pd.read_csv("spy_box_arbitrage_allpairs.csv", parse_dates=["date","expiration"])
res = res.sort_values("date")

plt.figure()
plt.scatter(res["date"], res["profit_sell"], s=6, label="profit_sell")
plt.scatter(res["date"], res["profit_buy"],  s=6, label="profit_buy")
plt.title("profits over time (all rows)")
plt.ylabel("profit per share")
plt.xlabel("date")
plt.legend()
plt.show()
