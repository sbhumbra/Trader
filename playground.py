import time

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d

import manager as M

coin_type = 'ETH'
num_iterations = 200
time_sleep = 0.1

iteration_interval = 3 * 60
forecasting_backwards_window = 15 * 60
forecasting_prediction_window = 15 * 60

plot_margin_price = 0.1  # +/- 10% on max/min price in plot
plot_margin_error = 2  # +/- on min/min error in plot
plot_gap = 3 * 60 * 60  # seconds, backwards from now
forecast_gap = 2 * 60 * 60  # seconds, backwards from now (time forecaster evaluated)
forecast_time = plot_gap - forecast_gap  # seconds, forwards from zero (time forecaster evaluated)

time_begin_default = 1520708240-3600*24*3
#1518305400 # use this for repeatable testing (flat market)

latest_time = int(time.time())
# need to make sure we don't go into the future...
time_begin = time_begin_default + forecast_time - (num_iterations * iteration_interval)

plt.figure(1)
title = plt.suptitle(coin_type)
ax_PreForecasting = plt.subplot(131)
ax_PostForecasting = plt.subplot(132)
ax_PredictionError = plt.subplot(133)

# Much faster to change data in lines (since axes are constant) than to clear and replot
ln_11 = None
ln_12 = None
ln_13 = None
ln_14 = None

ln_21 = None
ln_22 = None
ln_23 = None
ln_24 = None
ln_25 = None
ln_26 = None

ln_31 = None
ln_32 = None
ln_33 = None
ln_34 = None

plt.ion()
plt.show()
figManager = plt.get_current_fig_manager()
figManager.window.showMaximized()

flag_fake_exchange = True

A = M.Manager(time_begin,flag_fake_exchange)
A.list_of_coin_types = ['ETH']

for idx in range(0, num_iterations):
    now = time_begin + idx * iteration_interval
    title.set_text(coin_type + ' : Iteration ' + str(idx + 1) + ' of ' + str(num_iterations))

    # Get historic prices for plot window
    all_prices = A.exchange.get_price(now - plot_gap, coin_type, now)
    max_price = np.max(all_prices)
    min_price = np.min(all_prices)
    num_points = len(all_prices)
    all_prices_axis = np.linspace(0, (num_points - 1) * 60, num_points)
    f = interp1d(all_prices_axis, all_prices, kind='nearest')

    # Get historic prices for fitting window
    # Going 0 minutes in the past should give 1 data point (now), hence +1 on axis
    flag_in_range_lower = np.greater_equal(all_prices_axis, (forecast_time - forecasting_backwards_window))
    flag_in_range_upper = np.less_equal(all_prices_axis, forecast_time)
    flag_in_range = np.logical_and(flag_in_range_lower, flag_in_range_upper)
    fitting_prices = all_prices[flag_in_range]
    max_fitting_price = np.max(fitting_prices)
    min_fitting_price = np.min(fitting_prices)
    fitting_prices_axis = np.linspace(0, forecasting_backwards_window, int(forecasting_backwards_window / 60) + 1)
    if not (len(fitting_prices_axis) == len(fitting_prices)):
        print('Axis: ' + str(len(fitting_prices_axis)))
        print('Values: ' + str(len(fitting_prices)))
        raise Exception('Price fitting: axis and values should have the same length!!')
    else:
        coeff = np.polyfit(fitting_prices_axis, fitting_prices, 1)
        fitted_prices = coeff[1] + (coeff[0] * fitting_prices_axis)

    # Actual prices (at forecasting time)
    current_price = fitting_prices[-1]
    price_next_iteration = np.asscalar(f(forecast_time + iteration_interval))
    price_end_of_window = np.asscalar(f(forecast_time + forecasting_prediction_window))

    # Predict future prices
    predicted_prices_axis = np.linspace(0, forecasting_prediction_window, int(forecasting_prediction_window / 60) + 1)
    predicted_prices = current_price + (coeff[0] * predicted_prices_axis)
    predicted_price_next_iteration = current_price + (coeff[0] * iteration_interval)
    predicted_price_end_of_window = predicted_prices[-1]

    # Predicted/achieved returns
    predicted_return_next_iteration = 100 * (predicted_price_next_iteration - current_price) / current_price
    achieved_return_next_iteration = 100 * (price_next_iteration - current_price) / current_price
    prediction_error_next_iteration = achieved_return_next_iteration - predicted_return_next_iteration

    predicted_return_end_of_window = 100 * (predicted_price_end_of_window - current_price) / current_price
    achieved_return_end_of_window = 100 * (price_end_of_window - current_price) / current_price
    prediction_error_end_of_window = achieved_return_end_of_window - predicted_return_end_of_window

    flag_before_forecasting = all_prices_axis <= forecast_time
    # TODO Can we share lines between axes? Both have the current, fitted and predicted prices in common...
    if not ln_11:
        ln_11, = ax_PreForecasting.plot(all_prices_axis[flag_before_forecasting],
                                        all_prices[flag_before_forecasting], 'k')
        ln_12, = ax_PreForecasting.plot(forecast_time + predicted_prices_axis, predicted_prices, 'r--')
        ln_13, = ax_PreForecasting.plot((forecast_time - forecasting_backwards_window) + fitting_prices_axis,
                                        fitted_prices, 'r')
        ln_14, = ax_PreForecasting.plot([forecast_time], [current_price], 'ko')

        ln_21, = ax_PostForecasting.plot(all_prices_axis, all_prices, 'k')
        ln_22, = ax_PostForecasting.plot(forecast_time + predicted_prices_axis, predicted_prices, 'r--')
        ln_23, = ax_PostForecasting.plot((forecast_time - forecasting_backwards_window) + fitting_prices_axis,
                                         fitting_prices, 'r')
        ln_24, = ax_PostForecasting.plot([forecast_time], [current_price], 'ko')
        ln_25, = ax_PostForecasting.plot([forecast_time + iteration_interval], [predicted_price_next_iteration], 'ro')
        ln_26, = ax_PostForecasting.plot([forecast_time + forecasting_prediction_window],
                                         [predicted_price_end_of_window], 'bo')

        ln_31, = ax_PredictionError.plot(np.arange(num_iterations), np.full(num_iterations, np.nan), 'ro')
        error_history_next_iteration = ln_31.get_ydata()
        error_history_next_iteration[idx] = prediction_error_next_iteration
        ln_31.set_ydata(error_history_next_iteration)

        averaqe_error_next_iteration = np.nanmedian(error_history_next_iteration)
        ln_32, = ax_PredictionError.plot([0, num_iterations - 1],
                                         np.multiply(averaqe_error_next_iteration, [1, 1]), 'r--')

        ln_33, = ax_PredictionError.plot(np.arange(num_iterations), np.full(num_iterations, np.nan), 'bo')
        error_history_end_of_window = ln_33.get_ydata()
        error_history_end_of_window[idx] = prediction_error_end_of_window
        ln_33.set_ydata(error_history_end_of_window)

        averaqe_error_end_of_window = np.nanmedian(error_history_end_of_window)
        ln_34, = ax_PredictionError.plot([0, num_iterations - 1],
                                         np.multiply(averaqe_error_end_of_window, [1, 1]), 'b--')
    else:
        # Only the complete time history can change size: all others are fixed axes / a single point
        ln_11.set_xdata(all_prices_axis[flag_before_forecasting])
        ln_11.set_ydata(all_prices[flag_before_forecasting])
        ln_12.set_ydata(predicted_prices)
        ln_13.set_ydata(fitted_prices)
        ln_14.set_ydata([current_price])

        ln_21.set_xdata(all_prices_axis)
        ln_21.set_ydata(all_prices)
        ln_22.set_ydata(predicted_prices)
        ln_23.set_ydata(fitted_prices)
        ln_24.set_ydata([current_price])
        ln_25.set_ydata([predicted_price_next_iteration])
        ln_26.set_ydata([predicted_price_end_of_window])

        error_history_next_iteration = ln_31.get_ydata()
        error_history_next_iteration[idx] = prediction_error_next_iteration
        ln_31.set_ydata(error_history_next_iteration)

        averaqe_error_next_iteration = np.nanmedian(error_history_next_iteration)
        ln_32.set_ydata(np.multiply(averaqe_error_next_iteration, [1, 1]))

        error_history_end_of_window = ln_33.get_ydata()
        error_history_end_of_window[idx] = prediction_error_end_of_window
        ln_33.set_ydata(error_history_end_of_window)

        averaqe_error_end_of_window = np.nanmedian(error_history_end_of_window)
        ln_34.set_ydata(np.multiply(averaqe_error_end_of_window, [1, 1]))

    ax_PreForecasting.set_ylim(min_fitting_price * (1 - plot_margin_price), max_fitting_price * (1 + plot_margin_price))
    ax_PreForecasting.set_title('Expected: ' + "{:.3f}".format(predicted_return_next_iteration) + ' % next iteration' + \
                                '\nExpected: ' + "{:.3f}".format(predicted_return_end_of_window) + ' % end of window')

    ax_PostForecasting.set_ylim(min_price * (1 - plot_margin_price), max_price * (1 + plot_margin_price))
    ax_PostForecasting.set_title('Achieved: ' + "{:.3f}".format(achieved_return_next_iteration) + ' % next iteration' + \
                                 '\nAchieved: ' + "{:.3f}".format(achieved_return_end_of_window) + ' % end of window')

    min_error = np.minimum(np.nanmin(error_history_next_iteration),
                           np.nanmin(error_history_end_of_window)) - plot_margin_error
    max_error = np.maximum(np.nanmax(error_history_next_iteration),
                           np.nanmax(error_history_end_of_window)) + plot_margin_error
    plot_range = max(np.abs(min_error), np.abs(max_error))  # keeps zero line in the centre
    ax_PredictionError.set_ylim(-plot_range, plot_range)
    ax_PredictionError.set_title('Avg error: ' + "{:.3f}".format(averaqe_error_next_iteration) + ' % next iteration' + \
                                 '\nAvg error: ' + "{:.3f}".format(averaqe_error_end_of_window) + ' % end of window')

    flag_calculate_return = A.trade(now)
    print('')
    print('making loads')
    print('')
    if flag_calculate_return:
        A.calculate_return(now)

    plt.draw()
    plt.pause(0.01)

    time.sleep(time_sleep)
