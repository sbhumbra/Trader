import time


class Forecaster:
    def __init__(self, exchange):
        self.exchange = exchange

    def forecast(self, coin_type, timestamp):
        # What is the current time?
        now = int(time.time())

        # Get current price
        current_price = self.exchange.get_price(now, coin_type)

        # How far backwards in time do we go?
        time_backwards = 30 * 60

        # Get previous time
        dt = int(timestamp) - now

        # Get previous price
        last_price = self.exchange.get_price(now - time_backwards, coin_type)

        # Get price derivative
        dprice_dt = (current_price - last_price) / time_backwards

        # Linear extrapolation to get future price
        future_price = current_price + dprice_dt * dt
        return future_price
