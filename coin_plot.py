import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d


class Coin_Plot:
    def __init__(self, coin_type):
        self.plot_time_window_past = 1 * 60 * 60
        self.plot_time_window_future = 1 * 60 * 60
        self.plot_y_axis_margin = 0.2
        self.plot_time_window_fit = 15 * 60

        plt.figure(1)
        title = plt.suptitle(coin_type)
        self.ax = plt.subplot(111)
        self.ln_all_prices = None
        self.ln_past_prices = None
        self.ln_current_prices = None
        self.ln_predicted_prices = None
        self.ln_past_price = None
        self.ln_current_price = None
        self.ln_predicted_price = None
        plt.ion()
        plt.show()
        # figManager = plt.get_current_fig_manager()
        # figManager.window.showMaximized()

    def draw(self, exchange, timestamp, coin):
        # title.set_text(coin_type + ' : Iteration ' + str(idx + 1) + ' of ' + str(num_iterations))
        all_prices = exchange.get_price(timestamp - self.plot_time_window_past, coin.coin_type,
                                        timestamp + self.plot_time_window_future)
        max_price = np.max(all_prices)
        min_price = np.min(all_prices)
        num_points = len(all_prices)
        all_prices_axis = np.linspace(0, (num_points - 1) * 60, num_points)

        f_time = interp1d([timestamp - self.plot_time_window_past, timestamp + self.plot_time_window_future],
                          [0, (num_points - 1) * 60])

        past_price = coin.past_price
        past_price_time = np.asscalar(f_time(coin.past_price_time))

        current_price = coin.current_price
        current_price_time = np.asscalar(f_time(timestamp))

        predicted_price = coin.future_price
        predicted_price_time = np.asscalar((f_time(coin.future_price_time)))

        past_prices = [past_price - coin.past_price_gradient * self.plot_time_window_fit, past_price]
        past_prices_axis = [np.asscalar(f_time(coin.past_price_time - self.plot_time_window_fit)), past_price_time]

        current_prices = [current_price - coin.current_price_gradient * self.plot_time_window_fit, current_price]
        current_prices_axis = [np.asscalar(f_time(timestamp - self.plot_time_window_fit)), current_price_time]

        predicted_prices = [current_price, current_price + coin.current_price_gradient * self.plot_time_window_fit]
        predicted_prices_axis = [current_price_time, np.asscalar(f_time(timestamp + self.plot_time_window_fit))]

        if not self.ln_all_prices:
            self.ln_all_prices = self.ax.plot(all_prices_axis, all_prices, 'k')
            self.ln_past_prices = self.ax.plot(past_prices_axis, past_prices, 'b')
            self.ln_current_prices = self.ax.plot(current_prices_axis, current_prices, 'r')
            self.ln_predicted_prices = self.ax.plot(predicted_prices_axis, predicted_prices, 'r--')
            self.ln_past_price = self.ax.plot([past_price_time], [past_price], 'ko')
            self.ln_current_price = self.ax.plot([current_price_time], [current_price], 'ko')
            self.ln_predicted_price = self.ax.plot([predicted_price_time], [predicted_price], 'ro')
        else:
            self.set_data(self.ln_all_prices[0], all_prices_axis, all_prices)
            self.set_data(self.ln_past_prices[0], past_prices_axis, past_prices)
            self.set_data(self.ln_current_prices[0], current_prices_axis, current_prices)
            self.set_data(self.ln_predicted_prices[0], predicted_prices_axis, predicted_prices)
            self.set_data(self.ln_past_price[0], [past_price_time], [past_price])
            self.set_data(self.ln_current_price[0], [current_price_time], [current_price])
            self.set_data(self.ln_predicted_price[0], [predicted_price_time], [predicted_price])

        self.ax.set_ylim(min_price * (1 - self.plot_y_axis_margin), max_price * (1 + self.plot_y_axis_margin))
        plt.draw()
        plt.pause(0.01)

    def set_data(self, h, x, y):
        if len(x):
            h.set_xdata(x)

        if len(y):
            h.set_ydata(y)
