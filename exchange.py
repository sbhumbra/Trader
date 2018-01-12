import numpy as np


# any of these queries can timeout error - handle gracefully
# some exchanges are back to front too - handle here


class Exchange:
    def __init__(self, marketplace, buy_fee, sell_fee, haven_coin):
        self.marketplace = marketplace
        self.buy_fee = buy_fee
        self.sell_fee = sell_fee
        self.haven_coin = haven_coin

    def place_order(self, df_transaction, price=np.nan):
        # place order, then update transaction_id.  num_coin_bought and time_completed will still be empty
        # price to be used if we don't want market rate and instead want to place a limit order
        pass

    def query_order(self, df_transaction):
        # this time we must have the id - it checks the status of the transaction on the marketplace.
        # if gone thru, fills in num_coin_bought and time_completed
        # otherwise nothing.  Return bool true/false if gone thru or not
        pass

    def cancel_order(self, df_transaction):
        # cancel order with this transaction_id
        pass

    def get_price_history(self, coin, period, n_periods):
        # gets price history
        pass

    def get_supply(self, coin):
        # gets supply - will have to query coinmarketcap for this one
        pass
