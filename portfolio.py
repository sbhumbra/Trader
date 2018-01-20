import pandas as pd


# All prices in USD/EUR

class Portfolio:
    def __init__(self, exchange, filename=''):
        self.exchange = exchange
        # instantiate null ledger
        self.df_transaction_format = {'transaction_id': [], 'type_coin_sold': [], 'num_coin_sold': [],
                                      'type_coin_bought': [],
                                      'num_coin_bought': [], 'time_completed': []}

        self.df_coin_summary_format = {'type_coin': [], 'average_price_paid': [], 'num_coin': []}

        if filename:
            self.rebuild(filename)
        else:
            self.ledger = pd.DataFrame(data=self.df_transaction_format)
            self.coin_summary = pd.DataFrame(data=self.df_coin_summary_format)

    def rebuild(self, filename):
        # reconstruct ledger from file
        pass

    def record_transaction(self, df_transaction):
        # add transactions to the ledger
        pass

    def value_portfolio(self):
        # value the portfolio using the haven conversion
        # likely loop value_coin_holding
        pass

    def value_coin_holding(self, coin_type):
        # coin_type argument in case we just want the value of one coin
        pass

    def num_coin_holding(selfs, coin_type):
        # return number of coins held for a coin type
        pass

    def avg_price_paid_for_coin(self, coin_type):
        # return average price paid per coin
        pass

    def current_profit_loss_for_coin(self, coin_type):
        # percent difference between current market price per coin and average price paid per coin
        pass

    def update_avg_price_paid_for_coin(self, coin_type):
        # work out the average price paid per coin in fiat currency
        pass

    def update_num_coin_holding(self):
        # update coin tallies
        pass

    def update_avg_price_paid(self):
        # average price paid for all coins
        pass

    def deposit(self, eur_amount_paid, coin_type, coin_number):
        # insert a transaction that makes coin_type appear
        pass

    def withdraw(self, eur_amount_withdrawn, coin_type, coin_number):
        # insert a transaction that makes coin_type disappear
        pass
