import pandas as pd
import numpy as np

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
                                                                pd.DataFrame([[coin_type]], columns=['coin_type'])],
                                                               ignore_index=True)
                # last valid price 60 min buffer
                # last valid price 60 hour buffer
                # last valid price 60 day buffer
                # stored min/max values (can update realtime)
                # others??

    def rebuild(self, filename):
        pass

    def get_last_valid_price(self, coin_type):
        price = self.get_stats_last_valid_price_supply_property(coin_type, 'last_valid_price')
        timestamp = self.get_stats_last_valid_price_supply_property(coin_type, 'price_timestamp')
        return [price, timestamp]

    def set_last_valid_price(self, coin_type, price, timestamp):
        self.set_stats_last_valid_price_supply_property(coin_type, 'last_valid_price', price)
        self.set_stats_last_valid_price_supply_property(coin_type, 'price_timestamp', timestamp)

    def get_last_valid_supply(self, coin_type):
        supply = self.get_stats_last_valid_price_supply_property(coin_type, 'last_valid_supply')
        timestamp = self.get_stats_last_valid_price_supply_property(coin_type, 'supply_timestamp')
        return [supply, timestamp]

    def set_last_valid_supply(self, coin_type, supply, timestamp):
        self.set_stats_last_valid_price_supply_property(coin_type, 'last_valid_supply', supply)
        self.set_stats_last_valid_price_supply_property(coin_type, 'supply_timestamp', timestamp)

    def get_stats_last_valid_price_supply_property(self, coin_type, column):
        s = self.stats_last_valid_price_supply  # accessed as reference therefore same memory
        p = s.loc[s.loc[:, 'coin_type'] == coin_type, column]
        return np.asscalar(p.values)

    def set_stats_last_valid_price_supply_property(self, coin_type, column, value):
        s = self.stats_last_valid_price_supply  # accessed as reference therefore same memory
        s.loc[s.loc[:, 'coin_type'] == coin_type, column] = value
