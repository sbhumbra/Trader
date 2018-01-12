import numpy as np
import pandas as pd


class Portfolio:
    def __init__(self, coin_types, exchange):
        # make list of coins
        self.coins = []
        # instantiate null ledger
        d = {'transaction_id': [], 'type_coin_sold': [], 'num_coin_sold': [], 'type_coin_bought': [],
             'num_coin_bought': [], 'time_completed': []}
        self.ledger = pd.DataFrame(data=d)

P = Portfolio([], [])
print(P.ledger)