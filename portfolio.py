import pandas as pd
import numpy as np


# All prices in USD/EUR

class Portfolio:
    def __init__(self, exchange, filename=''):
        self.exchange = exchange
        # instantiate null ledger
        self.df_transaction_format = {'transaction_id': [], 'coin_type_sold': [], 'num_coin_sold': [],
                                      'coin_type_bought': [],
                                      'num_coin_bought': [], 'time_completed': []}

        self.df_coin_summary_format = {'coin_type': [], 'average_price_paid': [], 'num_coin': []}

        self.ledger = pd.DataFrame(data=self.df_transaction_format)
        self.coin_summary = pd.DataFrame(data=self.df_coin_summary_format)

        if filename:
            self.rebuild(filename)

    def rebuild(self, filename):
        # reconstruct ledger from file
        pass

    def record_transaction(self, df_transaction):
        #   Add transaction(s) to the ledger
        self.ledger = pd.concat([self.ledger, df_transaction], ignore_index=True)
        #   First update average pride paid (relies on past number of coins held)
        self.update_avg_price_paid_for_coin(df_transaction)
        #   ...now update number of coins held
        self.update_num_coin_holding(df_transaction)

    def value_portfolio(self):
        #   Total portfolio value
        #   Which coins do we hold?
        coin_types = self.coin_summary['coin_type']
        coin_types = coin_types.values.tolist()

        #   Loop through coins and add to total value
        portfolio_value = 0
        for coin_type in coin_types:
            portfolio_value += self.value_coin_holding(coin_type)

        return portfolio_value

    def value_coin_holding(self, coin_type):
        num_coins = self.num_coin_holding(coin_type)
        price_per_coin = self.exchange.get_price(coin_type)
        return num_coins * price_per_coin

    def num_coin_holding(self, coin_type):
        s = self.coin_summary  # accessed as reference therefore same memory
        try:
            p = s.loc[s.loc[:, 'coin_type'] == coin_type, 'num_coin']
            return np.asscalar(p.values)
        except:
            return 0

    def avg_price_paid_for_coin(self, coin_type):
        s = self.coin_summary  # accessed as reference therefore same memory
        try:
            p = s.loc[s.loc[:, 'coin_type'] == coin_type, 'average_price_paid']
            return np.asscalar(p.values)
        except:
            return np.nan

    def current_profit_loss_for_coin(self, coin_type):
        # percent difference between current market price per coin and average price paid per coin
        price_paid = self.avg_price_paid_for_coin(coin_type)
        if np.isnan(price_paid):
            return 0
        else:
            current_price = self.exchange.get_price(coin_type)
            return 100 * (current_price - price_paid) / price_paid

    def update_avg_price_paid_for_coin(self, df_transaction):
        #   Incrementally update average price paid using latest transaction
        pass

    def update_num_coin_holding(self, df_transaction):
        #   Incrementally update number of coins held using latest transaction
        pass

    def calculate_average_price_paid_per_coin(self):
        #   Calculate average price paid per coin from ledger
        pass

    def calculate_num_coin_holding(self):
        #   Calculate number of coins held from ledger
        pass

    def deposit(self, eur_amount_paid, coin_type, coin_number):
        # insert a transaction that makes coin_type appear
        pass

    def withdraw(self, eur_amount_withdrawn, coin_type, coin_number):
        # insert a transaction that makes coin_type disappear
        pass
