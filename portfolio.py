import pandas as pd
import numpy as np
import time


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

    def save(self, filename):
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
            balance = self.exchange.marketplace.fetch_balance()
            return balance[coin_type]['free']
            #p = s.loc[s.loc[:, 'coin_type'].astype(str) == coin_type, 'num_coin']
            #return np.asscalar(p.values)
        except:
            return 0

    def avg_price_paid_for_coin(self, coin_type):
        s = self.coin_summary  # accessed as reference therefore same memory
        try:
            p = s.loc[s.loc[:, 'coin_type'].astype(str) == coin_type, 'average_price_paid']
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
        df_t = df_transaction  # chained for readability
        s = self.coin_summary  # chained for readability

        #   First get all types of coin bought
        coin_types_bought = df_t['coin_type_bought']
        coin_types_bought = coin_types_bought.tolist()
        coin_types_bought = list(set(coin_types_bought))  # unique values

        #   For each type of coin bought, get set of transactions
        #   Work out total price paid and number bought
        #   Calculate new average price using old average price, previous number owned, and latest transaction
        for coin_type in coin_types_bought:
            df_c = df_t.loc[df_t.loc[:, 'coin_type_bought'].astype(str) == coin_type]  # transaction subset
            num_coins_bought = 0
            price_paid = 0
            for idx in df_c.index:
                num_coins_bought += df_c.loc[idx, 'num_coin_bought']
                coin_type_sold = df_c.loc[idx, 'coin_type_sold']
                num_coin_sold = df_c.loc[idx, 'num_coin_sold']
                time_sold = df_c.loc[idx, 'time_completed']
                price_paid += num_coin_sold * self.exchange.get_price(coin_type_sold, time_sold)

            num_coins_bought_prev = self.num_coin_holding(coin_type)
            avg_price_paid_prev = self.avg_price_paid_for_coin(coin_type)
            if np.isnan(avg_price_paid_prev):
                price_paid_prev = 0
            else:
                price_paid_prev = num_coins_bought_prev * avg_price_paid_prev

            avg_price_paid = (price_paid + price_paid_prev) / (num_coins_bought + num_coins_bought_prev)

            s_query = s.loc[s.loc[:, 'coin_type'].astype(str) == coin_type, 'average_price_paid']
            if s_query.any():
                s.loc[s.loc[:, 'coin_type'].astype(str) == coin_type, 'average_price_paid'] = avg_price_paid
            else:
                s = pd.concat(
                    [s, pd.DataFrame([[coin_type, avg_price_paid]], columns=['coin_type', 'average_price_paid'])],
                    ignore_index=True)

        self.coin_summary = s

    def update_num_coin_holding(self, df_transaction):
        #   Incrementally update number of coins held using latest transaction
        df_t = df_transaction  # chained for readability
        s = self.coin_summary  # chained for readability

        #   Iterate through all transactions, adding coins bought and subtracting coins sold
        for idx in df_t.index:
            coin_type_bought = df_t.loc[idx, 'coin_type_bought']
            num_coin_bought = df_t.loc[idx, 'num_coin_bought']
            num_coin_bought_curr = s.loc[s.loc[:, 'coin_type'].astype(str) == coin_type_bought, 'num_coin']
            flag_update = num_coin_bought_curr.values.any() and not np.isnan(num_coin_bought_curr.values)
            if flag_update:
                s.loc[s.loc[:, 'coin_type'].astype(str) == coin_type_bought, 'num_coin'] += num_coin_bought
            else:
                s.loc[s.loc[:, 'coin_type'].astype(str) == coin_type_bought, 'num_coin'] = num_coin_bought

            coin_type_sold = df_t.loc[idx, 'coin_type_sold']
            num_coin_sold = df_t.loc[idx, 'num_coin_sold']
            num_coin_sold_curr = s.loc[s.loc[:, 'coin_type'].astype(str) == coin_type_sold, 'num_coin']
            flag_update = num_coin_sold_curr.values.any() and not np.isnan(num_coin_sold_curr.values)
            if flag_update:
                s.loc[s.loc[:, 'coin_type'].astype(str) == coin_type_sold, 'num_coin'] -= num_coin_sold
            else:
                s.loc[s.loc[:, 'coin_type'].astype(str) == coin_type_sold, 'num_coin'] = -1 * num_coin_sold

        self.coin_summary = s

    def calculate_average_price_paid_per_coin(self):
        #   Calculate average price paid per coin from ledger
        pass

    def calculate_num_coin_holding(self):
        #   Calculate number of coins held from ledger
        pass

    def deposit(self, eur_amount_paid, coin_type, coin_number):
        #   Insert a transaction that makes coin_type appear
        #   Do this by treating EUR like a coin and recording the transaction
        #   EUR price on the exchange is 1
        df_t = pd.DataFrame({'transaction_id': [-1], 'coin_type_sold': ['EUR'], 'num_coin_sold': [eur_amount_paid],
                             'coin_type_bought': [coin_type],
                             'num_coin_bought': [coin_number], 'time_completed': [int(time.time())]})
        self.record_transaction(df_t)

    def withdraw(self, eur_amount_withdrawn, coin_type, coin_number):
        #   Insert a transaction that makes coin_type disappear
        df_t = pd.DataFrame({'transaction_id': [-1], 'coin_type_sold': [coin_type], 'num_coin_sold': [coin_number],
                             'coin_type_bought': ['EUR'],
                             'num_coin_bought': [eur_amount_withdrawn], 'time_completed': [int(time.time())]})
        #   Record transaction without updating average price paid per coin (since EUR isn't really a coin)
        self.ledger = pd.concat([self.ledger, df_t], ignore_index=True)
        self.update_num_coin_holding(df_t)
