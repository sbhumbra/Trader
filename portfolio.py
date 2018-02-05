import numpy as np
import copy


class Portfolio:
    def __init__(self, exchange):
        self.current_liquid_funds = 0
        self.current_holdings = {}
        exchange.value_portfolio(self)

    def calculate_return(self, exchange):
        # Update portfolio value after trading
        # Get previous state
        past_liquid_funds = self.current_liquid_funds
        past_holdings = copy.deepcopy(self.current_holdings)

        # Get previous total worth
        past_values = np.asarray([past_holdings[coin_type]['val'] for coin_type in past_holdings
                                  if not coin_type == exchange.haven_coin_type])
        past_portfolio_value = np.sum(past_values) + past_liquid_funds

        # Get new state
        exchange.value_portfolio(self)

        # Get current total worth
        current_coins = [coin_type for coin_type in self.current_holdings
                         if not coin_type == exchange.haven_coin_type]
        current_values = np.asarray([self.current_holdings[coin_type]['val'] for coin_type in self.current_holdings
                                     if not coin_type == exchange.haven_coin_type])
        current_portfolio_value = np.sum(current_values) + self.current_liquid_funds

        # Relative portfolio change
        relative_change = 100 * (current_portfolio_value - past_portfolio_value) / past_portfolio_value

        # Relative change per coin only makes sense for coins that we still hold
        relative_change_per_coin = 100 * np.asarray([((self.current_holdings[coin_type]['val'] /
                                                       past_holdings[coin_type]['val']) *
                                                      (self.current_holdings[coin_type]['num'] /
                                                       past_holdings[coin_type]['num']) - 1)
                                                     if coin_type in past_holdings else np.nan
                                                     for coin_type in self.current_holdings])
        relative_change_per_coin = np.round(relative_change_per_coin*100)/100

        print('Total change: ' + "{:.2f}".format(relative_change) + ' %')
        print("Coins are " + str(current_coins))
        print("Current holding: " + str(current_values).strip('[]'))
        print("Relative change: " + str(relative_change_per_coin).strip('[]') + ' %')
        print('')
        pass
