from backtesting import Strategy, Backtest
import pandas as pd
import pandas_ta as ta
import mplfinance as mpl

# Import other necessary libraries
from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=12)

contract = Stock(symbol='ALKEM', exchange='NSE', currency='INR')

class RenkoStrategy(Strategy):
    ema_1 = 7
    atr_box_size = 14

    def init(self):
        self.renko = mpl.renko(self.data.Close, self.atr_box_size)  # Correctly import the renko function
        self.ema1 = self.I(self.get_ema, self.data.Close, self.ema_1)
        self.position_count = 0

    def get_ema(self, closing_data, length):
        return ta.ema(closing_data, length)

    def next(self):
        current_renko_bar = self.renko[-1]
        previous_renko_bar = self.renko[-2]

        # If two green boxes are formed after minimum 4 red boxes and the price crosses the 7 period ema, go long.
        if current_renko_bar > previous_renko_bar and self.position_count >= 4 and self.data.Close > self.ema1[-1]:
            self.buy()

        # If two red boxes are formed preceded by minimum 4 green boxes and the price is above the 7 period ema, go short.
        elif current_renko_bar < previous_renko_bar and self.position_count >= 4 and self.data.Close < self.ema1[-1]:
            self.sell()

        # Close the position when the price closes below the 7 period ema if long, or closes above the 7 period ema if short.
        if self.position.is_long and self.data.Close < self.ema1[-1]:
            self.position.close()
        elif self.position.is_short and self.data.Close > self.ema1[-1]:
            self.position.close()

        self.position_count += 1

# Get historical data for the stock.
bars = ib.reqHistoricalData(
    contract, endDateTime='', durationStr='5 D',
    barSizeSetting='5 mins', whatToShow='TRADES', useRTH=True)

# Convert the historical data to a Pandas DataFrame.
df = util.df(bars)

# Rename columns to match Backtest's expected names
df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)

# Convert the data index to a datetime index.
df.index = pd.to_datetime(df.index)
print(df)

# Create a Backtest object and run the strategy.
bt = Backtest(df, RenkoStrategy, cash=1000000)
stats = bt.run()

# Print the backtesting results.
print(stats)
