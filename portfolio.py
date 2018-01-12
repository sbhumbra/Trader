import pandas as pd


# All prices in USD/EUR

class Portfolio:
    def __init__(self):
        # instantiate null ledger
        d = {'transaction_id': [], 'type_coin_sold': [], 'num_coin_sold': [], 'type_coin_bought': [],
             'num_coin_bought': [], 'time_completed': []}
        self.ledger = pd.DataFrame(data=d)

        d = {'type_coin': [], 'average_price_paid': [], 'num_coin': []}
        self.coin_summary = pd.DataFrame(data=d)

    def value_portfolio(self, haven):
        # value the portfolio using the haven conversion
        # likely loop value_coin_holding
        pass

    def value_coin_holding(self, haven, coin_type):
        # coin_type argument in case we just want the value of one coin
        pass

    def num_coin_holding(selfs, coin_type):
        # return number of coins held for a coin type
        pass

    def avg_price_paid_for_coin(self, coin_type):
        # return average price paid per coin
        pass

    def current_profit_loss_for_coin(self, haven, coin_type):
        # percent difference between current market price per coin and average price paid per coin
        pass

    def update_avg_price_paid_for_coin(self, haven, coin_type):
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

    def withdraw(self, coin_number, coin_type, eur_amount_withdrawn):
        # insert a transaction that makes coin_type disappear
        pass


P = Portfolio([], [])
print(P.ledger)
