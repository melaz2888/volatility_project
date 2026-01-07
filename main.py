from src.volatility import VolatilityAnalyzer

def main():
    # 1. Setup
    ticker = 'SPY'
    print(f"--- Starting Analysis for {ticker} ---")
    analyzer = VolatilityAnalyzer(ticker, start_date='2019-02-09', end_date='2025-12-23')

    # 2. Fetch & Compute
    analyzer.fetch_data()
    analyzer.calculate_rolling_volatility(windows=[20, 60, 120])
    analyzer.calculate_ewma_volatility(decay_factor=0.94)

    # 3. Event Analysis (Example: SVB Crisis March 2023)
    impact = analyzer.analyze_event_impact('2023-03-10', lookback_window=15)
    print("\n--- Event Impact Analysis ---")
    print(impact)

    # 4. Visualize
    print("\nPlotting results...")
    analyzer.plot_comparison()

if __name__ == "__main__":
    main()
