import time

import numpy as np


class Forecaster:
    def __init__(self, exchange):
        self.exchange = exchange

    def forecast(self, coin_type, timestamp):
        # What is the current time?
        now = int(time.time())

        # Get current price
        current_price = self.exchange.get_price(now, coin_type)

        # How far backwards in time do we go?
        time_backwards = 15 * 60

        # Get delta time between future and now
        dt = int(timestamp) - now

        # Get history of past prices
        price_history = self.exchange.get_price(now - time_backwards, coin_type, now)

        # Create time axis (1 minute spacing) for fit
        num_points = len(price_history)
        time_axis = np.linspace(0, (num_points - 1) * 60, num_points)

        # Linear fit
        coeff, residuals, _, _, _ = np.polyfit(time_axis, price_history, 1, full=True)
        dprice_dt = coeff[0]
        residuals = residuals[0]

        # Linear extrapolation to get future price
        future_price = current_price + dprice_dt * dt
        return future_price
