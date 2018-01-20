import pandas as pd


class CoinStats:
    def __init__(self, coin_types, filename=''):

        if filename:
            self.rebuild(filename)
        else:
            self.stats_last_valid_price_supply = pd.DataFrame(
                {'coin_type': [], 'last_valid_price': [], 'price_timestamp': [], 'last_valid_supply': [],
                 'supply_timestamp': []})
            for coin_type in coin_types:
                self.stats_last_valid_price_supply = pd.concat([self.stats_last_valid_price_supply,
                                                               pd.DataFrame([[coin_type]],columns=['coin_type'])],
                                                               ignore_index=True)
                # last valid price 60 min buffer
                # last valid price 60 hour buffer
                # last valid price 60 day buffer
                # stored min/max values (can update realtime)
                # others??

    def rebuild(self, filename):
        pass

    def get_last_valid_price(self, coin_type):
        pass

    def set_last_valid_price(self, coin_type, price):
        pass

    def get_last_valid_supply(self, coin_type):
        pass

    def set_last_valid_supply(self, coin_type, supply):
        pass
