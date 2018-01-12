import ccxt

import coin as c
import exchange as e
import forecaster as f
import portfolio as p


class Manager:
    def __init__(self):
        self.list_of_coins = ['BTC', 'ETH', 'BNB', 'BCC', 'LTC', 'NEO', 'USDT']  # coins tradeable with USDT on binance
        self.portfolio = p.Portfolio()
        self.haven_coin = c.Coin("USDT", ccxt.bitfinex())
        self.forecaster = f.Forecaster(self.haven_coin)  # to be able to go from usdt to real money
        self.exchange = e.Exchange(ccxt.binance(), 0.01 / 100, 0.01 / 100, self.haven_coin)
