import time


class Forecaster:
    def __init__(self, exchange):
        self.exchange = exchange

    def forecast(self, coin_type, timestamp):
        # timestamp (in future: vector of timestamps)
        time_prediction = 10*60
        now = int(time.time())
        dt = int(timestamp) - now
        current_price = self.exchange.get_price(coin_type)
        last_price = self.exchange.get_price(coin_type,now - time_prediction)
        dprice_dt = (current_price - last_price)/(time_prediction)
        future_price = current_price + dprice_dt * dt
        return future_price

    def validate(self, coin):
        # call with past timestamps to verify algorithm goodness
        # random sample timestamps
        # do forecast
        # check
        return True
