import numpy as np
import copy


class Portfolio:
    def __init__(self, timestamp, exchange):
        self.current_liquid_funds = 0
        self.current_holdings = {}
        self.initial_value = exchange.value_portfolio(timestamp, self)

    def calculate_return(self, timestamp, exchange):
        # Update portfolio value after trading
        current_portfolio_value = exchange.value_portfolio(timestamp, self)

        # Get coins and values
        current_coins = [coin_type for coin_type in self.current_holdings
                         if not coin_type == exchange.haven_coin_type]
        current_values = np.asarray([self.current_holdings[coin_type]['val'] for coin_type in self.current_holdings
                                     if not coin_type == exchange.haven_coin_type])

        # Relative portfolio change
        relative_change = 100 * (current_portfolio_value - self.initial_value) / self.initial_value

        print('Total change: ' + "{:.2f}".format(relative_change) + ' %')
        print("Coins are " + str(current_coins))
        print("Current holding: " + str(current_values).strip('[]'))
        # print("Relative change: " + str(relative_change_per_coin).strip('[]') + ' %')
        print('')
        pass
