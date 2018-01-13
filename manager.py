import ccxt
import time
import numpy as np

import coin as c
import exchange as e
import forecaster as f
import portfolio as p


class Manager:
    def __init__(self):
        self.list_of_coin_types = ['BTC', 'ETH', 'BNB', 'BCC', 'LTC', 'NEO']  # coins tradeable with USDT on binance
        self.haven_coin = c.Coin("USDT", ccxt.bitfinex())
        self.portfolio = p.Portfolio(self.haven_coin)
        self.forecaster = f.Forecaster(self.haven_coin)  # to be able to go from usdt to real money
        self.exchange = e.Exchange(ccxt.binance(), 0.01 / 100, 0.01 / 100, self.haven_coin)
        self.threshold_buy = 5
        self.threshold_sell = 5
        self.buy_value = 5

    def trade(self):
        now = int(time.time())
        future_time = now + 60 * 10
        NCoins = len(self.list_of_coin_types)
        coin_ids = np.linspace(1, NCoins, NCoins).astype('int')
        future_values = np.asarray([np.nan]) * NCoins
        current_values = np.asarray([np.nan]) * NCoins
        for idx, coin_type in enumerate(self.list_of_coin_types):
            future_values[idx] = self.portfolio.num_coin_holding(coin_type) * self.forecaster.forecast(coin_type,
                                                                                                       future_time)
            current_values[idx] = self.portfolio.value_coin_holding(coin_type)

        future_profit_loss = future_values - current_values

        # if a coin is predicted to make a loss and we don't hold it, we don't care
        # BUY: anything positive that's over threshold
        coins_to_buy = coin_ids[future_profit_loss >= self.threshold_buy]

        # SELL: anything we hold that's negative and over threshold
        coins_to_sell = coin_ids[(-1 * future_profit_loss >= self.threshold_sell) and (current_values > 0)]

        # make transaction batch

        # make loads of money

    def stop_trading(self):
        # stop trading so we can withdraw loads of money
        pass
