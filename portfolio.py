import numpy as np
import copy


class Portfolio:
    def __init__(self, exchange):
        self.current_liquid_funds = 0
        self.current_holdings = {}
        exchange.value_portfolio(self)
        self.past_liquid_funds = self.current_liquid_funds
        self.past_holdings = copy.deepcopy(self.current_holdings)

    def calculate_return(self, exchange):
        # # Update portfolio value after trading
        # exchange.value_portfolio(self)
        #
        # past_values = self.current_values
        # past_portfolio_value = np.sum(past_values) + past_liquid_funds
        #
        # self.current_values = np.multiply(current_prices, num_coins_held)
        # current_portfolio_value = np.sum(self.current_values) + self.total_liquid_funds
        #
        # relative_change_per_coin = 100 * np.divide(self.current_values - past_values, past_values)
        # relative_change = 100 * (current_portfolio_value - past_portfolio_value) / past_portfolio_value
        #
        # print('Current portfolio value: ' + str(current_portfolio_value) + ' ; ' + str(relative_change) + ' %')
        # print("Coins are " + str(self.list_of_coin_types))
        # print("Current holding: " + str(self.current_values).strip('[]'))
        # print("Previous holding: " + str(past_values).strip('[]'))
        # print("Relative change: " + str(relative_change_per_coin).strip('[]'))
        # print('')
        pass
