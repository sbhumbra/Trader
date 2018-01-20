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
        # value the portfolio using the haven conversion
        # likely loop value_coin_holding
        pass

    def value_coin_holding(self, coin_type):
        num_coins = self.num_coin_holding(coin_type)
        haven_price = self.exchange.get_price()  # shortcut for haven
        return num_coins * haven_price

    def num_coin_holding(selfs, coin_type):
        # return number of coins held for a coin type
        return 10

    def avg_price_paid_for_coin(self, coin_type):
        # return average price paid per coin
        pass

    def current_profit_loss_for_coin(self, coin_type):
        # percent difference between current market price per coin and average price paid per coin
        pass

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
