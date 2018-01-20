import time


class Forecaster:
    def __init__(self, exchange):
        self.exchange = exchange

    def forecast(self, coin_type, timestamp):
        # timestamp (in future: vector of timestamps)
        now = int(time.time())
        dt = int(timestamp) - now
        current_price = self.exchange.get_price(coin_type,now)
        last_price = self.exchange.get_price(coin_type,now - 10*60)
        dprice_dt = (current_price - last_price)/(10*60)
        future_price = current_price + dprice_dt * dt
        pass

    def validate(self, coin):
        # call with past timestamps to verify algorithm goodness
        # random sample timestamps
        # do forecast
        # check
        return True
