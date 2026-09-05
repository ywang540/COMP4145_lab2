import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import sys

# Import trading strategy functions
from trading_strategy import (
    get_stock_data, 
    calculate_moving_averages, 
    identify_golden_cross, 
    implement_strategy
)

class TradingDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Golden Cross Trading Strategy Dashboard")
        self.root.geometry("1400x900")
        
        # Load data
        self.data, self.positions = self.load_data()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)
        
        # Create tabs
        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.tab3 = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab1, text="📊 Price Chart")
        self.notebook.add(self.tab2, text="📈 Trade Statistics")
        self.notebook.add(self.tab3, text="📋 Detailed Trades")
        
        # Build tabs
        self.build_price_chart_tab()
        self.build_statistics_tab()
        self.build_trades_tab()
    
    def load_data(self):
        """Load and process trading data"""
        try:
            data = get_stock_data("MSFT")
        except:
            print("Using sample data...")
            data = None
        
        if data is not None and not data.empty:
            data = calculate_moving_averages(data)
            data = identify_golden_cross(data)
            positions = implement_strategy(data)
            return data, positions
        
        return None, None
    
    def build_price_chart_tab(self):
        """Build price chart tab"""
        if self.data is None:
            label = ttk.Label(self.tab1, text="Unable to load data", font=("Arial", 14))
            label.pack()
            return
        
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # Plot close price
        ax.plot(self.data.index, self.data['Close'], label='Close Price', 
               color='black', linewidth=2, alpha=0.7)
        
        # Plot moving averages
        ax.plot(self.data.index, self.data['MA50'], label='50-Day MA', 
               color='blue', linewidth=1.5, alpha=0.8)
        ax.plot(self.data.index, self.data['MA200'], label='200-Day MA', 
               color='red', linewidth=1.5, alpha=0.8)
        
        # Plot buy signals
        buy_points = self.data[self.data['GoldenCross'] == True]
        if not buy_points.empty:
            ax.scatter(buy_points.index, buy_points['Close'], 
                      color='green', marker='^', s=200, label='Buy Signal', 
                      zorder=5, edgecolors='darkgreen', linewidth=2)
        
        # Plot sell signals
        if not self.positions.empty:
            sell_dates = pd.to_datetime(self.positions['SellDate'])
            sell_prices = self.positions['SellPrice'].values
            ax.scatter(sell_dates, sell_prices, 
                      color='red', marker='v', s=200, label='Sell Signal', 
                      zorder=5, edgecolors='darkred', linewidth=2)
        
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Price ($)', fontsize=12)
        ax.set_title('MSFT Stock Price and Trading Signals', fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        
        canvas = FigureCanvasTkAgg(fig, master=self.tab1)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def build_statistics_tab(self):
        """Build statistics tab"""
        if self.positions is None or self.positions.empty:
            label = ttk.Label(self.tab2, text="No trading signals detected", 
                            font=("Arial", 14))
            label.pack()
            return
        
        # Calculate statistics
        total_trades = len(self.positions)
        win_trades = len(self.positions[self.positions['ProfitPct'] > 0])
        loss_trades = total_trades - win_trades
        win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
        
        avg_profit = self.positions['ProfitPct'].mean()
        avg_win = self.positions[self.positions['ProfitPct'] > 0]['ProfitPct'].mean() if win_trades > 0 else 0
        avg_loss = self.positions[self.positions['ProfitPct'] <= 0]['ProfitPct'].mean() if loss_trades > 0 else 0
        
        avg_holding = self.positions['HoldingDays'].mean()
        total_return = self.positions['ProfitPct'].sum()
        
        target_reached = len(self.positions[self.positions['SellReason'] == 'Target reached'])
        max_period = len(self.positions[self.positions['SellReason'] == 'Max holding period'])
        
        # Create frame for stats
        stats_frame = ttk.Frame(self.tab2)
        stats_frame.pack(fill="both", expand=False, padx=10, pady=10)
        
        # Create stats display
        stats_data = [
            ("Total Trades", total_trades),
            ("Win Rate", f"{win_rate:.2f}%"),
            ("Average Profit", f"{avg_profit:.2f}%"),
            ("Total Return", f"{total_return:.2f}%"),
            ("", ""),
            ("Winning Trades", win_trades),
            ("Losing Trades", loss_trades),
            ("Avg Win", f"{avg_win:.2f}%"),
            ("Avg Loss", f"{avg_loss:.2f}%"),
            ("", ""),
            ("Avg Holding Days", f"{avg_holding:.0f}"),
            ("Target Reached", target_reached),
            ("Max Period Exits", max_period),
        ]
        
        for label_text, value in stats_data:
            if label_text == "":
                ttk.Separator(stats_frame, orient='horizontal').pack(fill='x', pady=5)
            else:
                frame = ttk.Frame(stats_frame)
                frame.pack(fill='x', pady=5)
                ttk.Label(frame, text=label_text + ":", font=("Arial", 11)).pack(side='left', anchor='w')
                ttk.Label(frame, text=str(value), font=("Arial", 11, "bold")).pack(side='right', anchor='e')
        
        # Add charts
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Histogram of profits
        ax1.hist(self.positions['ProfitPct'], bins=15, color='skyblue', 
                edgecolor='black', alpha=0.7)
        ax1.axvline(avg_profit, color='red', linestyle='--', linewidth=2, 
                   label=f'Average: {avg_profit:.2f}%')
        ax1.axvline(0, color='black', linestyle='-', linewidth=1)
        ax1.set_xlabel('Profit (%)', fontsize=11)
        ax1.set_ylabel('Frequency', fontsize=11)
        ax1.set_title('Distribution of Trade Profits', fontsize=12, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Pie chart
        sizes = [win_trades, loss_trades]
        colors = ['#2ecc71', '#e74c3c']
        explode = (0.05, 0.05)
        ax2.pie(sizes, explode=explode, labels=[f'Wins ({win_trades})', f'Losses ({loss_trades})'], 
               autopct='%1.1f%%', colors=colors, startangle=90, textprops={'fontsize': 11})
        ax2.set_title('Win/Loss Ratio', fontsize=12, fontweight='bold')
        
        canvas = FigureCanvasTkAgg(fig, master=self.tab2)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
    
    def build_trades_tab(self):
        """Build detailed trades tab"""
        if self.positions is None or self.positions.empty:
            label = ttk.Label(self.tab3, text="No trading signals detected", 
                            font=("Arial", 14))
            label.pack()
            return
        
        # Create frame for table
        frame = ttk.Frame(self.tab3)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create treeview
        columns = ('Buy Date', 'Buy Price', 'Sell Date', 'Sell Price', 'Holding Days', 'Profit %', 'Exit Reason')
        tree = ttk.Treeview(frame, columns=columns, height=15, show='headings')
        
        # Define column headings and widths
        for col in columns:
            tree.column(col, width=150, anchor='center')
            tree.heading(col, text=col)
        
        # Add data to tree
        for idx, row in self.positions.iterrows():
            values = (
                row['BuyDate'].strftime('%Y-%m-%d'),
                f"${row['BuyPrice']:.2f}",
                row['SellDate'].strftime('%Y-%m-%d'),
                f"${row['SellPrice']:.2f}",
                int(row['HoldingDays']),
                f"{row['ProfitPct']:.2f}%",
                row['SellReason']
            )
            
            # Color code based on profit
            if row['ProfitPct'] > 0:
                tree.insert('', 'end', values=values, tags=('win',))
            else:
                tree.insert('', 'end', values=values, tags=('loss',))
        
        # Configure tags for coloring
        tree.tag_configure('win', foreground='green')
        tree.tag_configure('loss', foreground='red')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

if __name__ == '__main__':
    root = tk.Tk()
    app = TradingDashboard(root)
    root.mainloop()
