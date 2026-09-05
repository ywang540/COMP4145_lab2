"""
Golden Cross Trading Strategy Dashboard - Streamlit App
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import sys
import os

# Set page config
st.set_page_config(
    page_title="Trading Strategy Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom styling
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# Import trading strategy functions
from trading_strategy import (
    generate_sample_data,
    calculate_moving_averages,
    identify_golden_cross,
    implement_strategy
)

# Load data
@st.cache_data
def load_trading_data():
    """Load data and run trading strategy"""
    data = generate_sample_data()
    data = calculate_moving_averages(data)
    data = identify_golden_cross(data)
    positions = implement_strategy(data)
    return data, positions

# Title and description
st.title("📈 Golden Cross Trading Strategy Dashboard")
st.markdown("**MSFT Stock Analysis - 5 Year Backtest**")
st.markdown("---")

# Load data
data, positions = load_trading_data()

# Create tabs
tab1, tab2, tab3 = st.tabs(["📊 Price Chart", "📈 Trade Statistics", "📋 Detailed Trades"])

# ===== TAB 1: PRICE CHART =====
with tab1:
    st.subheader("Stock Price with Moving Averages and Trade Signals")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Plot close price
    ax.plot(data.index, data['Close'], label='Close Price', color='black', linewidth=2, alpha=0.7)
    
    # Plot moving averages
    ax.plot(data.index, data['MA50'], label='50-Day MA', color='blue', linewidth=1.5, alpha=0.8)
    ax.plot(data.index, data['MA200'], label='200-Day MA', color='red', linewidth=1.5, alpha=0.8)
    
    # Plot buy signals (golden cross points)
    buy_points = data[data['GoldenCross'] == True]
    if not buy_points.empty:
        ax.scatter(buy_points.index, buy_points['Close'], 
                  color='green', marker='^', s=200, label='Buy Signal', zorder=5, edgecolors='darkgreen', linewidth=2)
    
    # Plot sell signals from positions
    if not positions.empty:
        sell_dates = pd.to_datetime(positions['SellDate'])
        sell_prices = positions['SellPrice'].values
        ax.scatter(sell_dates, sell_prices, 
                  color='red', marker='v', s=200, label='Sell Signal', zorder=5, edgecolors='darkred', linewidth=2)
    
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Price ($)', fontsize=12)
    ax.set_title('MSFT Stock Price and Trading Signals', fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Format x-axis
    fig.autofmt_xdate()
    plt.tight_layout()
    
    st.pyplot(fig)
    
    # Chart info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Price", f"${data['Close'].iloc[-1]:.2f}")
    with col2:
        st.metric("50-Day MA", f"${data['MA50'].iloc[-1]:.2f}")
    with col3:
        st.metric("200-Day MA", f"${data['MA200'].iloc[-1]:.2f}")

# ===== TAB 2: TRADE STATISTICS =====
with tab2:
    st.subheader("Overall Trade Statistics")
    
    if positions.empty:
        st.info("No trading signals detected")
    else:
        # Calculate statistics
        total_trades = len(positions)
        win_trades = len(positions[positions['ProfitPct'] > 0])
        loss_trades = total_trades - win_trades
        win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
        
        avg_profit = positions['ProfitPct'].mean()
        avg_win = positions[positions['ProfitPct'] > 0]['ProfitPct'].mean() if win_trades > 0 else 0
        avg_loss = positions[positions['ProfitPct'] <= 0]['ProfitPct'].mean() if loss_trades > 0 else 0
        
        avg_holding = positions['HoldingDays'].mean()
        total_return = positions['ProfitPct'].sum()
        
        target_reached = len(positions[positions['SellReason'] == 'Target reached'])
        max_period = len(positions[positions['SellReason'] == 'Max holding period'])
        
        # Display statistics in cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Trades", total_trades, help="Total number of completed trades")
        with col2:
            st.metric("Win Rate", f"{win_rate:.2f}%", help="Percentage of winning trades")
        with col3:
            st.metric("Average Profit", f"{avg_profit:.2f}%", help="Average profit per trade")
        with col4:
            st.metric("Total Return", f"{total_return:.2f}%", help="Sum of all trade returns")
        
        # More details
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.metric("Winning Trades", win_trades)
        with col6:
            st.metric("Losing Trades", loss_trades)
        with col7:
            st.metric("Avg Win", f"{avg_win:.2f}%")
        with col8:
            st.metric("Avg Loss", f"{avg_loss:.2f}%")
        
        # Additional info
        col9, col10, col11 = st.columns(3)
        
        with col9:
            st.metric("Avg Holding Days", f"{avg_holding:.0f} days")
        with col10:
            st.metric("Target Reached", target_reached)
        with col11:
            st.metric("Max Period Exits", max_period)
        
        # Distribution chart
        st.markdown("---")
        st.subheader("Profit Distribution")
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Histogram of profit percentages
            fig1, ax1 = plt.subplots(figsize=(7, 5))
            ax1.hist(positions['ProfitPct'], bins=15, color='skyblue', edgecolor='black', alpha=0.7)
            ax1.axvline(avg_profit, color='red', linestyle='--', linewidth=2, label=f'Average: {avg_profit:.2f}%')
            ax1.axvline(0, color='black', linestyle='-', linewidth=1)
            ax1.set_xlabel('Profit (%)', fontsize=11)
            ax1.set_ylabel('Frequency', fontsize=11)
            ax1.set_title('Distribution of Trade Profits', fontsize=12, fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            st.pyplot(fig1)
        
        with col_chart2:
            # Pie chart of win/loss
            fig2, ax2 = plt.subplots(figsize=(7, 5))
            sizes = [win_trades, loss_trades]
            colors = ['#2ecc71', '#e74c3c']
            explode = (0.05, 0.05)
            ax2.pie(sizes, explode=explode, labels=[f'Wins ({win_trades})', f'Losses ({loss_trades})'], 
                   autopct='%1.1f%%', colors=colors, startangle=90, textprops={'fontsize': 11})
            ax2.set_title('Win/Loss Ratio', fontsize=12, fontweight='bold')
            st.pyplot(fig2)

# ===== TAB 3: DETAILED TRADES =====
with tab3:
    st.subheader("Detailed Trade Records")
    
    if positions.empty:
        st.info("No trading signals detected")
    else:
        # Display table
        display_df = positions.copy()
        display_df['BuyDate'] = pd.to_datetime(display_df['BuyDate']).dt.strftime('%Y-%m-%d')
        display_df['SellDate'] = pd.to_datetime(display_df['SellDate']).dt.strftime('%Y-%m-%d')
        display_df['BuyPrice'] = display_df['BuyPrice'].apply(lambda x: f"${x:.2f}")
        display_df['SellPrice'] = display_df['SellPrice'].apply(lambda x: f"${x:.2f}")
        display_df['ProfitPct'] = display_df['ProfitPct'].apply(lambda x: f"{x:.2f}%")
        
        # Filter columns for display
        display_df = display_df[['BuyDate', 'BuyPrice', 'SellDate', 'SellPrice', 'HoldingDays', 'ProfitPct', 'SellReason']]
        display_df.columns = ['Buy Date', 'Buy Price', 'Sell Date', 'Sell Price', 'Holding Days', 'Profit %', 'Exit Reason']
        display_df = display_df.reset_index(drop=True)
        display_df.index = display_df.index + 1
        
        st.dataframe(display_df, use_container_width=True)
        
        # Show individual trade details
        st.markdown("---")
        st.subheader("Trade Details")
        
        for idx, trade in positions.iterrows():
            # Color based on profit
            if trade['ProfitPct'] > 0:
                emoji = "🟢"
                color = "green"
            elif trade['ProfitPct'] < 0:
                emoji = "🔴"
                color = "red"
            else:
                emoji = "🟡"
                color = "orange"
            
            with st.expander(f"{emoji} Trade #{idx + 1}: {trade['BuyDate'].strftime('%Y-%m-%d')} → {trade['SellDate'].strftime('%Y-%m-%d')} ({trade['ProfitPct']:.2f}%)"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Buy Information**")
                    st.write(f"📅 Date: {trade['BuyDate'].strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"💰 Price: ${trade['BuyPrice']:.2f}")
                
                with col2:
                    st.write("**Sell Information**")
                    st.write(f"📅 Date: {trade['SellDate'].strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"💰 Price: ${trade['SellPrice']:.2f}")
                
                col3, col4, col5 = st.columns(3)
                
                with col3:
                    st.write("**Trade Result**")
                    st.write(f"📊 Profit: {trade['ProfitPct']:.2f}%")
                
                with col4:
                    st.write("**Duration**")
                    st.write(f"⏱️ {trade['HoldingDays']} days")
                
                with col5:
                    st.write("**Exit Reason**")
                    st.write(f"🎯 {trade['SellReason']}")

st.markdown("---")
st.markdown("**Dashboard created with Streamlit** | Data generated from trading strategy backtest")
