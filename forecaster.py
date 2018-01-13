import numpy as np
import time
import coin as C


class Forecaster:
    def __init__(self, haven_coin):
        self.haven_coin = haven_coin

    def forecast(self, coin_type, timestamp):
        # timestamp (in future: vector of timestamps)
        now = int(time.time())
        dt = int(timestamp) - now
        coin = C.Coin(coin_type)
        current_price = coin.price(self.haven_coin)
        last_prices = coin.price_history(self.haven_coin, '1m', 10)
        dPrice = current_price - last_prices[1]
        future_price = current_price + dPrice * dt / (10 * 60)
        pass

    def validate(self, coin):
        # call with past timestamps to verify algorithm goodness
        # random sample timestamps
        # do forecast
        # check
        return True
