import time

import numpy as np


class Forecaster:
    def __init__(self, exchange):
        self.exchange = exchange

    def forecast(self, coin_type, future_timestamp, now_timestamp):
        # Get current price
        current_price = self.exchange.get_price(now_timestamp, coin_type)

        # How far backwards in time do we go?
        time_backwards = 15 * 60

        # Get delta time between future and now
        dt = int(future_timestamp) - now_timestamp

        # Get history of past prices
        price_history = self.exchange.get_price(now_timestamp - time_backwards, coin_type, now_timestamp)

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
