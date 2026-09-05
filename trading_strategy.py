import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time

# Download 5 years of MSFT data
def get_stock_data(ticker, period="5y", retries=3):
    for attempt in range(retries):
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)
            return data
        except Exception as e:
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 30  # 30s, 60s, 90s
                print(f"Rate limited. Retry attempt {attempt + 1}/{retries}. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Failed to download data after {retries} attempts. Using sample data instead...")
                return generate_sample_data()

# Generate sample historical data for demonstration
def generate_sample_data():
    dates = pd.date_range(end=datetime.now(), periods=1260, freq='D')  # ~5 years of trading days
    np.random.seed(42)
    
    # Generate realistic price movement
    returns = np.random.normal(0.0003, 0.015, len(dates))
    prices = 100 * np.exp(np.cumsum(returns))
    
    data = pd.DataFrame({
        'Open': prices * (1 + np.random.uniform(-0.01, 0.01, len(prices))),
        'High': prices * (1 + np.random.uniform(0, 0.02, len(prices))),
        'Low': prices * (1 + np.random.uniform(-0.02, 0, len(prices))),
        'Close': prices,
        'Volume': np.random.randint(20000000, 50000000, len(prices))
    }, index=dates)
    
    print("Using generated sample data for demonstration...")
    return data

# Calculate moving averages
def calculate_moving_averages(data):
    data['MA50'] = data['Close'].rolling(window=50).mean()
    data['MA200'] = data['Close'].rolling(window=200).mean()
    return data

# Identify golden cross (buy signals)
def identify_golden_cross(data):
    data['Signal'] = 0  # Initialize signal column with 0
    # Golden Cross occurs when MA50 crosses above MA200
    data['GoldenCross'] = (data['MA50'] > data['MA200']) & (data['MA50'].shift(1) <= data['MA200'].shift(1))
    return data

# Implement trading strategy
def implement_strategy(data):
    positions = []

    # Need at least 200 days to calculate the 200-day MA
    data = data.iloc[200:].copy()

    buy_dates = data[data['GoldenCross'] == True].index.tolist()

    for buy_date in buy_dates:
        # Get buy price
        buy_price = data.loc[buy_date, 'Close']

        # Calculate target sell price (15% profit)
        target_price = buy_price * 1.15

        # Set maximum holding period
        max_sell_date = buy_date + pd.Timedelta(days=60)

        # Get data slice for potential sell period
        sell_period = data.loc[buy_date:max_sell_date].copy()

        # Check if target price is reached during the period
        target_reached = sell_period[sell_period['Close'] >= target_price]

        if not target_reached.empty:
            # Sell at first date target is reached
            sell_date = target_reached.index[0]
            sell_price = target_reached.loc[sell_date, 'Close']
            sell_reason = "Target reached"
        else:
            # Sell at end of maximum holding period
            sell_date_candidates = sell_period.index.tolist()
            if sell_date_candidates:
                sell_date = sell_date_candidates[-1]
                sell_price = data.loc[sell_date, 'Close']
                sell_reason = "Max holding period"
            else:
                # Skip if no valid sell date (should not happen in practice)
                continue

        # Calculate holding period in calendar days
        holding_days = (sell_date - buy_date).days

        # Calculate profit
        profit_pct = (sell_price / buy_price - 1) * 100

        positions.append({
            'BuyDate': buy_date,
            'BuyPrice': buy_price,
            'SellDate': sell_date,
            'SellPrice': sell_price,
            'HoldingDays': holding_days,
            'ProfitPct': profit_pct,
            'SellReason': sell_reason
        })

    return pd.DataFrame(positions)

# Analyze the results
def analyze_results(positions):
    if positions.empty:
        return "No trading signals detected"

    # Summary statistics
    total_trades = len(positions)
    win_trades = len(positions[positions['ProfitPct'] > 0])
    loss_trades = total_trades - win_trades
    win_rate = win_trades / total_trades * 100 if total_trades > 0 else 0

    avg_profit = positions['ProfitPct'].mean()
    avg_win = positions[positions['ProfitPct'] > 0]['ProfitPct'].mean() if win_trades > 0 else 0
    avg_loss = positions[positions['ProfitPct'] <= 0]['ProfitPct'].mean() if loss_trades > 0 else 0

    avg_holding = positions['HoldingDays'].mean()

    target_reached = len(positions[positions['SellReason'] == 'Target reached'])
    max_period = len(positions[positions['SellReason'] == 'Max holding period'])

    print("\n===== Trading Strategy Results (Golden Cross)=====")
    print(f"Total Trades: {total_trades}")
    print(f"Winning Trades: {win_trades} ({win_rate:.2f}%)")
    print(f"Losing Trades: {loss_trades}")
    print(f"Average Profit: {avg_profit:.2f}%")

    return positions

# Main function
def main():
    # Get stock data
    data = get_stock_data("MSFT")

    # Calculate moving averages
    data = calculate_moving_averages(data)

    # Identify golden cross
    data = identify_golden_cross(data)

    # Implement strategy
    positions = implement_strategy(data)

    # Analyze results
    analyze_results(positions)

    # Return the detailed positions dataframe
    return positions

positions = main()
print("\nDetailed Trades:")
print(positions.to_string())