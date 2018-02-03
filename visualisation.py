import time
import manager as M
import numpy as np
import matplotlib.pyplot as plt

A = M.Manager()

iteration_time = 3 * 60
time_backwards = 15 * 60
future_prediction = 60 * 60

coin_type = 'NEO'

gap_range = 180 * 60
gap_forecast = 120 * 60

plt.figure(1)
ax1 = plt.subplot(121)
ax2 = plt.subplot(122)

plt.ion()
plt.show()

for idx in range(0, 100):
    now = 1517620657 + idx * iteration_time
    print(idx)
    ax1.clear()
    ax2.clear()

    prices = A.exchange.get_price(now - gap_range, coin_type, now)  # last hour of prices
    num_points = len(prices)
    time_axis = np.linspace(0, (num_points - 1) * 60, num_points)

    forecast_time = now - gap_forecast
    historical_prices = A.exchange.get_price(forecast_time - time_backwards, coin_type, forecast_time)
    num_points = len(historical_prices)
    historical_time_axis = np.linspace(0, (num_points - 1) * 60, num_points)
    coeff = np.polyfit(historical_time_axis, historical_prices, 1)

    prediction_time_axis = np.linspace(0, 59 * 60, 60)
    predicted_prices = historical_prices[-1] + (coeff[0] * prediction_time_axis)

    predicted_price_at_next_iteration = historical_prices[-1] + (coeff[0] * (iteration_time))

    predicted_price_in_future = historical_prices[-1] + (coeff[0] * (future_prediction))

    flag_select = time_axis <= (gap_range - gap_forecast)

    ax1.plot(time_axis[flag_select], prices[flag_select], 'k')
    ax1.plot((gap_range - gap_forecast) + prediction_time_axis, predicted_prices, 'r--')
    ax1.plot((gap_range - gap_forecast) + historical_time_axis - time_backwards,
             (coeff[0] * historical_time_axis) + coeff[1], 'r')
    ax1.plot([gap_range - gap_forecast], [historical_prices[-1]], 'ro')
    plt.title('Expected: ' + str(
        100 * (predicted_price_in_future - historical_prices[-1]) / historical_prices[-1]) + ' % in future')

    ax2.plot(time_axis, prices, 'k')
    ax2.plot((gap_range - gap_forecast) + prediction_time_axis, predicted_prices, 'r--')
    ax2.plot((gap_range - gap_forecast) + historical_time_axis - time_backwards,
             (coeff[0] * historical_time_axis) + coeff[1], 'r')
    ax2.plot([gap_range - gap_forecast], [historical_prices[-1]], 'ro')
    ax2.plot([(gap_range - gap_forecast) + iteration_time], [predicted_price_at_next_iteration], 'ko')

    plt.draw()
    plt.pause(0.001)

    time.sleep(1)
