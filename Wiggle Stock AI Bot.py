import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import robin_stocks.robinhood as rs
from matplotlib.dates import date2num
from mplfinance.original_flavor import candlestick_ohlc

def wiggle_indicator(data, window=20, buy_threshold=0.5, sell_threshold=-0.5):
    # calculate moving average
    data['ma'] = data['Close'].rolling(window=window).mean()

    # calculate wiggle value
    data['wiggle'] = (data['Close'] - data['ma']) / data['Close'].rolling(window=window).std()
    
    # create buy and sell signals
    data['signal'] = np.where(data['wiggle'] > buy_threshold, 1, 0)
    data['signal'] = np.where(data['wiggle'] < sell_threshold, -1, data['signal'])
    
    return data

# get ticker from user
ticker = input("Enter the stock ticker: ")
timeframe = "1m"

# load data
data = yf.download(ticker, interval=timeframe)

# get last day data
last_day_data = data.loc[(data.index >= (data.index[-1] - pd.DateOffset(days=1)))]

# run wiggle indicator with more sensitive values
wiggle_data = wiggle_indicator(last_day_data, window=5, buy_threshold=0.9, sell_threshold=-0.9)

# Prepare data for candlestick plot
wiggle_data['date'] = wiggle_data.index
wiggle_data_ohlc = wiggle_data[['date', 'Open', 'High', 'Low', 'Close']]
wiggle_data_ohlc = wiggle_data_ohlc.reset_index(drop=True)
wiggle_data_ohlc['date'] = wiggle_data_ohlc['date'].map(date2num)

# Set the style to dark theme
plt.style.use('dark_background')

# Create subplots
fig, ax = plt.subplots(2,1, figsize=(12,8), sharex=True)

# Candlestick plot
candlestick_ohlc(ax[0], wiggle_data_ohlc.values, width=0, colorup='green', colordown='red')
ax[0].set_title(f'{ticker} Candlestick Plot')
ax[0].set_ylabel('Price')
ax[0].xaxis_date()
ax[0].set_xlim(wiggle_data.index[0].replace(hour=9),wiggle_data.index[-1].replace(hour=16))
ax[0].axvline(wiggle_data.index[0].replace(hour=9), color='black', linestyle='--')
ax[0].axvline(wiggle_data.index[-1].replace(hour=16), color='black', linestyle='--')

# Wiggle plot
wiggle_data_no_yellow = wiggle_data.loc[wiggle_data['signal'] != 0]
ax[1].scatter(wiggle_data_no_yellow.index, wiggle_data_no_yellow['wiggle'], c=wiggle_data_no_yellow['signal'], cmap='RdYlGn')
ax[1].set_xlabel('Date')
ax[1].set_ylabel('Wiggle')
ax[1].set_title(f'{ticker} Wiggle Indicator {timeframe}')

# Uncomment this plot if you want to display the chart only & not trade
# plt.show()

#Log in to robin_stocks
rs.login()

# get current price of stock
current_price = rs.stocks.get_crypto(ticker)['last_trade_price']

# check for buy signals and execute buy order
if 1 in wiggle_data['signal'].values:
    quantity = 1 / current_price
    rs.orders.order_sell_crypto(ticker, current_price, quantity)
    print(f'Bought {quantity} shares of {ticker} worth {1} at {current_price}')

# check for sell signals and execute sell order
elif -1 in wiggle_data['signal'].values:
    quantity = 1 / current_price
    rs.orders.order_sell_crypto(ticker, current_price, quantity)
    print(f'Sold {quantity} shares of {ticker} worth {1} at {current_price}')

plt.show()

# logout of Robinhood account
rs.logout()
