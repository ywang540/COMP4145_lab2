#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Suppress conda errors
os.environ['CONDA_NO_PLUGINS'] = '1'

import pandas as pd
import json
from trading_strategy import (
    generate_sample_data,
    calculate_moving_averages, 
    identify_golden_cross, 
    implement_strategy
)

# Load and process data
print("Generating sample trading data...")
data = generate_sample_data()

print("Processing data...")
data = calculate_moving_averages(data)
data = identify_golden_cross(data)
positions = implement_strategy(data)

# Prepare data for JSON
data_json = data[['Close', 'MA50', 'MA200', 'GoldenCross']].copy()
data_json['Date'] = data_json.index.strftime('%Y-%m-%d')
data_json = data_json.reset_index(drop=True)

# Convert to list of dicts
chart_data = []
for idx, row in data_json.iterrows():
    chart_data.append({
        'date': row['Date'],
        'close': float(row['Close']),
        'ma50': float(row['MA50']) if pd.notna(row['MA50']) else None,
        'ma200': float(row['MA200']) if pd.notna(row['MA200']) else None,
        'signal': bool(row['GoldenCross'])
    })

# Prepare trade data
trades_data = []
for idx, row in positions.iterrows():
    trades_data.append({
        'id': idx + 1,
        'buyDate': row['BuyDate'].strftime('%Y-%m-%d'),
        'buyPrice': float(row['BuyPrice']),
        'sellDate': row['SellDate'].strftime('%Y-%m-%d'),
        'sellPrice': float(row['SellPrice']),
        'holdingDays': int(row['HoldingDays']),
        'profitPct': float(row['ProfitPct']),
        'reason': row['SellReason']
    })

# Calculate statistics
total_trades = len(positions)
win_trades = len(positions[positions['ProfitPct'] > 0])
loss_trades = total_trades - win_trades
win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
avg_profit = float(positions['ProfitPct'].mean()) if not positions.empty else 0
avg_win = float(positions[positions['ProfitPct'] > 0]['ProfitPct'].mean()) if win_trades > 0 else 0
avg_loss = float(positions[positions['ProfitPct'] <= 0]['ProfitPct'].mean()) if loss_trades > 0 else 0
avg_holding = float(positions['HoldingDays'].mean()) if not positions.empty else 0
total_return = float(positions['ProfitPct'].sum()) if not positions.empty else 0

stats = {
    'totalTrades': total_trades,
    'winTrades': win_trades,
    'lossTrades': loss_trades,
    'winRate': win_rate,
    'avgProfit': avg_profit,
    'avgWin': avg_win,
    'avgLoss': avg_loss,
    'avgHoldingDays': avg_holding,
    'totalReturn': total_return,
    'targetReached': len(positions[positions['SellReason'] == 'Target reached']) if not positions.empty else 0,
    'maxPeriodExits': len(positions[positions['SellReason'] == 'Max holding period']) if not positions.empty else 0
}

print("Creating HTML dashboard...")

# Create HTML dashboard
html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Golden Cross Trading Strategy Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .tab-button {
            flex: 1;
            padding: 15px;
            border: none;
            background: white;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s ease;
            color: #333;
        }
        
        .tab-button:hover {
            background: #f0f0f0;
        }
        
        .tab-button.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .tab-content {
            display: none;
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }
        
        .tab-content.active {
            display: block;
        }
        
        .chart-container {
            width: 100%;
            height: 600px;
            margin-bottom: 30px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-card .label {
            font-size: 14px;
            opacity: 0.8;
            margin-bottom: 10px;
        }
        
        .stat-card .value {
            font-size: 28px;
            font-weight: bold;
        }
        
        .trades-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }
        
        .trades-table th {
            background: #f5f5f5;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #ddd;
        }
        
        .trades-table td {
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        
        .trades-table tr:hover {
            background: #f9f9f9;
        }
        
        .profit {
            color: #27ae60;
            font-weight: 600;
        }
        
        .loss {
            color: #e74c3c;
            font-weight: 600;
        }
        
        .trade-row.win {
            background: #f0fff4 !important;
        }
        
        .trade-row.loss {
            background: #fff5f5 !important;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .badge.target {
            background: #e8f5e9;
            color: #27ae60;
        }
        
        .badge.maxperiod {
            background: #fff3e0;
            color: #f39c12;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 Golden Cross Trading Strategy Dashboard</h1>
            <p>MSFT Stock Analysis - 5 Year Backtest</p>
        </div>
        
        <div class="tabs">
            <button class="tab-button active" onclick="showTab(0)">📊 Price Chart</button>
            <button class="tab-button" onclick="showTab(1)">📈 Trade Statistics</button>
            <button class="tab-button" onclick="showTab(2)">📋 Detailed Trades</button>
        </div>
        
        <!-- Tab 1: Price Chart -->
        <div id="tab-0" class="tab-content active">
            <h2>Stock Price with Moving Averages and Trade Signals</h2>
            <div id="priceChart" class="chart-container"></div>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="label">Current Price</div>
                    <div class="value">$""" + f"{data['Close'].iloc[-1]:.2f}" + """</div>
                </div>
                <div class="stat-card">
                    <div class="label">50-Day MA</div>
                    <div class="value">$""" + f"{data['MA50'].iloc[-1]:.2f}" + """</div>
                </div>
                <div class="stat-card">
                    <div class="label">200-Day MA</div>
                    <div class="value">$""" + f"{data['MA200'].iloc[-1]:.2f}" + """</div>
                </div>
            </div>
        </div>
        
        <!-- Tab 2: Statistics -->
        <div id="tab-1" class="tab-content">
            <h2>Overall Trade Statistics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="label">Total Trades</div>
                    <div class="value">""" + str(stats['totalTrades']) + """</div>
                </div>
                <div class="stat-card">
                    <div class="label">Win Rate</div>
                    <div class="value">""" + f"{stats['winRate']:.2f}%" + """</div>
                </div>
                <div class="stat-card">
                    <div class="label">Average Profit</div>
                    <div class="value">""" + f"{stats['avgProfit']:.2f}%" + """</div>
                </div>
                <div class="stat-card">
                    <div class="label">Total Return</div>
                    <div class="value">""" + f"{stats['totalReturn']:.2f}%" + """</div>
                </div>
                <div class="stat-card">
                    <div class="label">Winning Trades</div>
                    <div class="value">""" + str(stats['winTrades']) + """</div>
                </div>
                <div class="stat-card">
                    <div class="label">Losing Trades</div>
                    <div class="value">""" + str(stats['lossTrades']) + """</div>
                </div>
                <div class="stat-card">
                    <div class="label">Average Win</div>
                    <div class="value">""" + f"{stats['avgWin']:.2f}%" + """</div>
                </div>
                <div class="stat-card">
                    <div class="label">Average Loss</div>
                    <div class="value">""" + f"{stats['avgLoss']:.2f}%" + """</div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 30px;">
                <div>
                    <div id="profitChart" style="height: 400px;"></div>
                </div>
                <div>
                    <div id="winLossChart" style="height: 400px;"></div>
                </div>
            </div>
        </div>
        
        <!-- Tab 3: Detailed Trades -->
        <div id="tab-2" class="tab-content">
            <h2>Detailed Trade Records</h2>
            <table class="trades-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Buy Date</th>
                        <th>Buy Price</th>
                        <th>Sell Date</th>
                        <th>Sell Price</th>
                        <th>Holding Days</th>
                        <th>Profit %</th>
                        <th>Exit Reason</th>
                    </tr>
                </thead>
                <tbody>
"""

# Add trade rows
for trade in trades_data:
    row_class = "win" if trade['profitPct'] > 0 else "loss"
    profit_class = "profit" if trade['profitPct'] > 0 else "loss"
    badge_class = "target" if trade['reason'] == "Target reached" else "maxperiod"
    badge_text = "Target" if trade['reason'] == "Target reached" else "Max Period"
    
    html_content += f"""                    <tr class="trade-row {row_class}">
                        <td>{trade['id']}</td>
                        <td>{trade['buyDate']}</td>
                        <td>${trade['buyPrice']:.2f}</td>
                        <td>{trade['sellDate']}</td>
                        <td>${trade['sellPrice']:.2f}</td>
                        <td>{trade['holdingDays']}</td>
                        <td class="{profit_class}">{trade['profitPct']:.2f}%</td>
                        <td><span class="badge {badge_class}">{badge_text}</span></td>
                    </tr>
"""

html_content += """                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        const chartData = """ + json.dumps(chart_data) + """;
        const tradesData = """ + json.dumps(trades_data) + """;
        const stats = """ + json.dumps(stats) + """;
        
        function showTab(index) {
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            const buttons = document.querySelectorAll('.tab-button');
            buttons.forEach(btn => btn.classList.remove('active'));
            
            document.getElementById('tab-' + index).classList.add('active');
            buttons[index].classList.add('active');
            
            if (index === 1 && !window.statsChartDrawn) {
                drawProfitChart();
                drawWinLossChart();
                window.statsChartDrawn = true;
            }
        }
        
        function drawPriceChart() {
            const dates = chartData.map(d => d.date);
            const closes = chartData.map(d => d.close);
            const ma50 = chartData.map(d => d.ma50);
            const ma200 = chartData.map(d => d.ma200);
            
            const buyDates = [];
            const buyPrices = [];
            const sellDates = [];
            const sellPrices = [];
            
            chartData.forEach(d => {
                if (d.signal) {
                    buyDates.push(d.date);
                    buyPrices.push(d.close);
                }
            });
            
            tradesData.forEach(trade => {
                sellDates.push(trade.sellDate);
                sellPrices.push(trade.sellPrice);
            });
            
            const trace1 = {
                x: dates,
                y: closes,
                name: 'Close Price',
                type: 'scatter',
                mode: 'lines',
                line: {color: '#000000', width: 2}
            };
            
            const trace2 = {
                x: dates,
                y: ma50,
                name: '50-Day MA',
                type: 'scatter',
                mode: 'lines',
                line: {color: '#0066cc', width: 1.5}
            };
            
            const trace3 = {
                x: dates,
                y: ma200,
                name: '200-Day MA',
                type: 'scatter',
                mode: 'lines',
                line: {color: '#cc0000', width: 1.5}
            };
            
            const trace4 = {
                x: buyDates,
                y: buyPrices,
                name: 'Buy Signal',
                type: 'scatter',
                mode: 'markers',
                marker: {color: '#00cc00', size: 10, symbol: 'triangle-up', line: {color: '#00aa00', width: 2}}
            };
            
            const trace5 = {
                x: sellDates,
                y: sellPrices,
                name: 'Sell Signal',
                type: 'scatter',
                mode: 'markers',
                marker: {color: '#ff0000', size: 10, symbol: 'triangle-down', line: {color: '#aa0000', width: 2}}
            };
            
            const layout = {
                title: 'MSFT Stock Price and Trading Signals',
                xaxis: {title: 'Date'},
                yaxis: {title: 'Price ($)'},
                hovermode: 'x unified',
                plot_bgcolor: '#f8f8f8'
            };
            
            Plotly.newPlot('priceChart', [trace1, trace2, trace3, trace4, trace5], layout);
        }
        
        function drawProfitChart() {
            const profits = tradesData.map(d => d.profitPct);
            
            const trace = {
                x: profits,
                type: 'histogram',
                nbinsx: 15,
                marker: {color: '#5b9fff'}
            };
            
            const layout = {
                title: 'Distribution of Trade Profits',
                xaxis: {title: 'Profit (%)'},
                yaxis: {title: 'Frequency'},
                plot_bgcolor: '#f8f8f8'
            };
            
            Plotly.newPlot('profitChart', [trace], layout);
        }
        
        function drawWinLossChart() {
            const labels = ['Wins', 'Losses'];
            const values = [stats.winTrades, stats.lossTrades];
            const colors = ['#27ae60', '#e74c3c'];
            
            const trace = {
                labels: labels,
                values: values,
                type: 'pie',
                marker: {colors: colors}
            };
            
            const layout = {
                title: 'Win/Loss Ratio'
            };
            
            Plotly.newPlot('winLossChart', [trace], layout);
        }
        
        drawPriceChart();
    </script>
</body>
</html>
"""

# Save HTML file
output_path = os.path.join(os.path.dirname(__file__), 'trading_dashboard.html')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✅ Dashboard created successfully!")
print(f"📂 File location: {output_path}")
print(f"🌐 Open the file in your web browser to view the dashboard")
