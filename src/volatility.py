import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


class VolatilityAnalyzer:
    def __init__(self, ticker: str, start_date: str, end_date: str):
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.data: pd.DataFrame | None = None

    def fetch_data(self):
        """Fetches SPY price data AND VIX 'Fear Index' data."""
        print(f"Fetching data for {self.ticker}...")
        
        # 1. Download Asset Data (e.g., SPY)
        self.data = yf.download(self.ticker, start=self.start_date, end=self.end_date, progress=False)
        
        # Handle MultiIndex cleanup (Standardizing formatting)
        if isinstance(self.data.columns, pd.MultiIndex):
            if 'Adj Close' in self.data.columns.get_level_values(0):
                self.data = self.data.xs('Adj Close', level=0, axis=1)
            else:
                self.data = self.data.xs('Close', level=0, axis=1)
        else:
            col = 'Adj Close' if 'Adj Close' in self.data.columns else 'Close'
            self.data = self.data[[col]].copy()
            self.data.rename(columns={col: 'Price'}, inplace=True)
            
        if 'Price' not in self.data.columns: self.data.columns = ['Price']

        # 2. Download VIX Data (The "Fear Gauge")
        print("Fetching VIX (Implied Volatility) data...")
        vix_data = yf.download("^VIX", start=self.start_date, end=self.end_date, progress=False)
        
        # Clean VIX data similar to Asset data
        if isinstance(vix_data.columns, pd.MultiIndex):
            if 'Close' in vix_data.columns.get_level_values(0):
                vix_vals = vix_data.xs('Close', level=0, axis=1)
            else:
                vix_vals = vix_data.iloc[:, 0] # Fallback
        else:
            vix_vals = vix_data['Close'] if 'Close' in vix_data.columns else vix_data['Adj Close']
            
        # Merge VIX into main dataframe (Align dates)
        # Note: VIX is 20.0, we want 0.20 to match our calc, so divide by 100
        self.data['VIX_Close'] = vix_vals / 100.0

        # 3. Calculate Returns
        self.data['Log_Ret'] = np.log(self.data['Price'] / self.data['Price'].shift(1))
        self.data.dropna(inplace=True)
        
        return self.data

    def calculate_rolling_volatility(self, windows: list[int] = [20, 60, 120]) -> pd.DataFrame:
        """Calculates annualized rolling volatility for standard windows."""
        if self.data is None:
            raise ValueError("No data loaded. Call fetch_data() first.")
        ann_factor = np.sqrt(252)
        for w in windows:
            col_name = f'Vol_{w}d'
            self.data[col_name] = self.data['Log_Ret'].rolling(window=w).std() * ann_factor
        return self.data

    def calculate_ewma_volatility(self, decay_factor: float = 0.94) -> pd.DataFrame:
        """Calculates EWMA volatility (RiskMetrics style)."""
        if self.data is None:
            raise ValueError("No data loaded. Call fetch_data() first.")
        ann_factor = np.sqrt(252)
        self.data['Squared_Ret'] = self.data['Log_Ret'] ** 2
        self.data['EWMA_Var'] = self.data['Squared_Ret'].ewm(alpha=(1 - decay_factor), adjust=False).mean()
        self.data['Vol_EWMA'] = np.sqrt(self.data['EWMA_Var']) * ann_factor
        return self.data

    def analyze_event_impact(self, event_date: str, lookback_window: int = 10):
        """Compares realized volatility before/after a specific date."""
        if self.data is None:
            raise ValueError("No data loaded. Call fetch_data() first.")

        target = pd.to_datetime(event_date)
        if getattr(self.data.index, "tz", None) is not None and self.data.index.tz is not None:
            target = target.tz_localize(self.data.index.tz)

        try:
            idx_loc = self.data.index.get_indexer([target], method='nearest')[0]
            event_idx = self.data.index[idx_loc]

            start_loc = max(0, idx_loc - lookback_window)
            end_loc = min(len(self.data), idx_loc + lookback_window)

            pre_event = self.data.iloc[start_loc:idx_loc]['Log_Ret']
            post_event = self.data.iloc[idx_loc:end_loc]['Log_Ret']

            pre_vol = pre_event.std() * np.sqrt(252)
            post_vol = post_event.std() * np.sqrt(252)

            return {
                "Event Date": getattr(event_idx, "date", lambda: event_idx)(),
                f"Pre ({lookback_window}d)": round(pre_vol * 100, 2),
                f"Post ({lookback_window}d)": round(post_vol * 100, 2),
                "Change": round((post_vol - pre_vol) * 100, 2)
            }
        except Exception as e:
            return f"Error analyzing date {event_date}: {e}"

    def plot_comparison(self):
        if self.data is None or self.data.empty: return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True, gridspec_kw={'height_ratios': [2, 1]})
        
        # --- Top Plot: Volatility Regimes ---
        # 1. Realized Volatility (What actually happened)
        if 'Vol_120d' in self.data.columns:
            ax1.plot(self.data.index, self.data['Vol_120d'], label='120d Realized (Trend)', color='black', linestyle='--', alpha=0.7)
        if 'Vol_EWMA' in self.data.columns:
            ax1.plot(self.data.index, self.data['Vol_EWMA'], label='EWMA Realized (Fast)', color='red', linewidth=1.5)
            
        # 2. Implied Volatility (What market feared - The VIX)
        if 'VIX_Close' in self.data.columns:
            ax1.plot(self.data.index, self.data['VIX_Close'], label='VIX (Market Fear)', color='green', alpha=0.5, linewidth=1)

        ax1.set_title(f'Realized Volatility vs. Market Fear (VIX): {self.ticker}')
        ax1.set_ylabel('Annualized Volatility')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # --- Bottom Plot: The "Fear Premium" (VIX - EWMA) ---
        # Positive = Market is paying premium for insurance (Fear > Reality)
        # Negative = Market is complacent (Fear < Reality) -> DANGER ZONE
        if 'VIX_Close' in self.data.columns and 'Vol_EWMA' in self.data.columns:
            spread = self.data['VIX_Close'] - self.data['Vol_EWMA']
            
            # Color coding: Green (Premium) vs Red (Complacency)
            ax2.fill_between(self.data.index, spread, 0, where=(spread >= 0), color='green', alpha=0.3, label='Fear Premium (Expensive Puts)')
            ax2.fill_between(self.data.index, spread, 0, where=(spread < 0), color='red', alpha=0.3, label='Complacency (Cheap Puts)')
            
            ax2.plot(self.data.index, spread, color='black', linewidth=0.5)
            ax2.axhline(0, color='black', linestyle='-', linewidth=0.5)
            ax2.set_ylabel('Spread (VIX - EWMA)')
            ax2.set_title('The Variance Risk Premium (Implied - Realized)')
            ax2.legend(loc='upper left')
            ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()