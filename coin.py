import numpy as np


class Coin:
    def __init__(self, coin_type):
        self.coin_type = coin_type
        self.num_coin_held = np.nan
        self.current_price = np.nan
        self.future_price = np.nan
        self.current_price_gradient = np.nan
        self.past_price_gradient = np.nan

    def update_num_coin_held(self, exchange):
        self.num_coin_held = exchange.num_coin_holding(self.coin_type)

    def update_current_price(self, exchange, now_timestamp):
        self.current_price = exchange.get_price(now_timestamp, self.coin_type)

    def forecast_future_price(self, forecaster, now_timestamp, future_timestamp):
        self.future_price = forecaster.forecast(self.coin_type, now_timestamp, future_timestamp)
        self.current_price_gradient = 100 * (self.future_price - self.current_price) / self.current_price

    def calculate_past_price_gradient(self, exchange, past_timestamp, time_window):
        # Get history of past prices
        price_history = exchange.get_price(past_timestamp - time_window, self.coin_type, past_timestamp)

        # Create time axis (1 minute spacing) for fit
        num_points = len(price_history)
        time_axis = np.linspace(0, (num_points - 1) * 60, num_points)

        # Linear fit
        coeff, residuals, _, _, _ = np.polyfit(time_axis, price_history, 1, full=True)
        past_price_gradient = coeff[0]  # dPrice/dt
        avg_past_price = coeff[1]  # since time origin is 0

        self.past_price_gradient = 100 * past_price_gradient / avg_past_price  # %
