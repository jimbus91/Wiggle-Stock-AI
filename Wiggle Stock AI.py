import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import robin_stocks.robinhood as r
from matplotlib.dates import date2num
from datetime import datetime, timedelta
from mplfinance.original_flavor import candlestick_ohlc

def wiggle_indicator(data, window=20, buy_threshold=0.5, sell_threshold=-0.5):
    data_copy = data.copy()
    data_copy.loc[:, 'ma'] = data_copy['Close'].rolling(window=window).mean()
    data_copy.loc[:, 'wiggle'] = (data_copy['Close'] - data_copy['ma']) / data_copy['Close'].rolling(window=window).std()
    data_copy.loc[:, 'signal'] = np.where(data_copy['wiggle'] > buy_threshold, 1, 0)
    data_copy.loc[:, 'signal'] = np.where(data_copy['wiggle'] < sell_threshold, -1, data_copy['signal'])
    return data_copy

# Log in to Robinhood
r.login(username='email', password='password', expiresIn=86400, by_sms=True)

# Get account information
account_info = r.account.load_phoenix_account(info=None)

# Get your portfolio's total value:

buying_power = account_info['account_buying_power']['amount']
print(f"Your buying power is: ${buying_power}")

r.logout()

def get_stock_data(ticker):
    today = datetime.now()
    # If it's a weekend or before the market opens, adjust to the last trading day
    if today.weekday() >= 5 or today.hour < 9:  # Before market opens or on weekends
        # Adjust to the last trading day
        if today.weekday() == 5:  # Saturday
            offset_days = 1
        elif today.weekday() == 6:  # Sunday
            offset_days = 2
        else:  # Weekday but before market open
            offset_days = 0
        today -= timedelta(days=offset_days)
    
    # Fetching only the last trading day's data
    start_date = today.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    end_date = start_date + timedelta(days=1)
    
    df = yf.download(ticker, start=start_date, end=end_date, interval='1m')
    if not df.empty:
        df.index = df.index.tz_localize(None)  # Remove timezone information
    else:
        print(f"Failed to download data for {ticker}.")
        return None

    return df

while True:
    ticker = input("Enter the stock ticker symbol (or type 'exit' to quit): ").upper()
    if ticker.lower() == 'exit':
        break

    data = get_stock_data(ticker)

    if data is not None:
        last_day_data = data.loc[(data.index >= (data.index[-1] - pd.DateOffset(days=1)))]
        wiggle_data = wiggle_indicator(last_day_data, window=5, buy_threshold=0.9, sell_threshold=-0.9)
        
        # Prepare data for wiggle plot
        wiggle_data['date'] = wiggle_data.index
        wiggle_data_ohlc = wiggle_data[['date', 'Open', 'High', 'Low', 'Close']]
        wiggle_data_ohlc = wiggle_data_ohlc.reset_index(drop=True)
        wiggle_data_ohlc['date'] = wiggle_data_ohlc['date'].map(date2num)
        
        # Set the style to dark background
        plt.style.use('dark_background')
        
        # Create subplots
        fig, ax = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # Candlestick plot
        candlestick_ohlc(ax[0], wiggle_data_ohlc.values, width=0.0006, colorup='green', colordown='red')
        ax[0].xaxis_date()
        ax[0].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        ax[0].set_title(f'{ticker} Candlestick Plot')
        ax[0].set_ylabel('Price')
        plt.xticks(rotation=45)
        
        # Wiggle plot
        wiggle_data_no_yellow = wiggle_data.loc[wiggle_data['signal'] != 0]
        ax[1].scatter(wiggle_data_no_yellow.index, wiggle_data_no_yellow['wiggle'], c=wiggle_data_no_yellow['signal'], cmap='RdYlGn', marker='o')
        ax[1].set_ylabel('Wiggle')
        ax[1].set_title(f'{ticker} Wiggle Indicator')
        
        plt.tight_layout()
        # plt.show()    # Uncomment this plt.show() if you want to disable automatic trading

        # Optional Trading Section (Commented out by default)
        # if 1 in wiggle_data['signal'].values:
        #      r.orders.order_buy_stock_by_price(ticker, 1)
        #      print(f'Placed an order to buy $1 worth of {ticker}')
        # elif -1 in wiggle_data['signal'].values:
        #      r.orders.order_sell_stock_by_price(ticker, 1)
        #      print(f'Placed an order to sell $1 worth of {ticker}')

        plt.show()  # This ensures the chart is always shown regardless of the trading option

        # r.logout()   # Logout of Robinhood account
            
    else:
        print("Invalid ticker.", end=" ")
