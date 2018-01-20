import numpy as np
import coinstats as C
import time
import pandas as pd
import ccxt


# any of these queries can timeout error - handle gracefully
# some exchanges are back to front too - handle here

class Exchange:
    def __init__(self, coin_types, marketplace=ccxt.binance(), haven_marketplace=ccxt.bitfinex(), buy_fee=0, sell_fee=0,
                 haven_coin_type='USDT',
                 filename_coinstats='', flag_fake_exchange=False):

        #   Get coin-coin exchange rates from this marketplace (e.g. binance)
        self.marketplace = marketplace

        #   Transaction fees on coin-coin marketplace
        #   These are fraction i.e. buy_price = (1 + buy_fee)*quoted_buy_price
        #                           sell_price = (1 - sell_fee)*quoted_sell_price
        self.buy_fee = buy_fee
        self.sell_fee = sell_fee

        #   Get haven-FIAT exchange rate from this marketplace (e.g. bitfinex)
        self.haven_marketplace = haven_marketplace
        self.haven_coin_type = haven_coin_type

        #   Create repository for past data and methods for querying it
        #   e.g. last valid price / max / min / average in window / variance in window / etc.
        all_coin_types = coin_types.copy()
        all_coin_types.append(haven_coin_type)
        self.coinstats = C.CoinStats(all_coin_types, filename_coinstats)

        #   If TRUE, place/query/sell order functions won't actually use the exchange order API
        self.flag_fake_exchange = flag_fake_exchange

        #   Tolerances (in seconds) within which the exchange will return the last valid value if a query fails
        self.price_time_query_tolerance = 1
        self.supply_time_query_tolerance = 60
        # self.exchange_rate_time_query_tolerance = 1 # not stored yet..

    def place_order(self, df_transaction, price=np.nan):
        # place order, then update transaction_id.  num_coin_bought and time_completed will still be empty
        # price to be used if we don't want market rate and instead want to place a limit order
        if self.flag_fake_exchange:
            # Assign all NaN transaction IDs a value
            num_transactions = len(df_transaction.index)
            for idx in range(0, num_transactions):
                df_transaction.at[idx, 'transaction_id'] = idx
        else:
            pass

    def query_order(self, df_transaction):
        # This time we must have the id - it checks the status of the transaction on the marketplace.
        # If gone through, fills in num_coin_bought and time_completed
        #   otherwise nothing.
        # df_transaction is a dataframe and can contain many orders
        # It is passed as reference
        # Don't query an order if it's already been completed
        # Return True/False if ALL orders completed
        num_transactions = len(df_transaction.index)
        flag_all_orders_completed = np.full(num_transactions, False)
        if self.flag_fake_exchange:
            for idx in range(0, num_transactions):
                try:
                    if not flag_all_orders_completed[idx]:
                        coin_sell_price = (1 - self.sell_fee) * self.get_price(df_transaction.at[idx, 'type_coin_sold'])
                        coin_buy_price = (1 + self.buy_fee) * self.get_price(df_transaction.at[idx, 'type_coin_bought'])
                        exchange_rate = coin_sell_price / coin_buy_price # ($/H) / ($/B) -> B/H
                        num_coin_bought = exchange_rate * df_transaction.at[idx, 'num_coin_sold']
                        df_transaction.at[idx, 'num_coin_bought'] = num_coin_bought
                        df_transaction.at[idx, 'time_completed'] = int(time.time())
                        flag_all_orders_completed[idx] = True
                except:
                    pass
        else:
            pass
        return all(flag_all_orders_completed)

    def cancel_order(self, df_transaction):
        # cancel incomplete orders
        if self.flag_fake_exchange:
            id_transactions_to_cancel = []
            num_transactions = len(df_transaction.index)
            for idx in range(0, num_transactions):
                if np.isnan(df_transaction.at[idx, 'time_completed']):
                    id_transactions_to_cancel.append(idx)

            df_transaction.drop(df_transaction.index[id_transactions_to_cancel],inplace=True)
        else:
            pass

    def get_price(self, coin_type='haven', timestamps=np.nan):
        if coin_type=='haven':
            return self.get_price(self.haven_coin_type,timestamps)
        else:
            pass

    def get_supply(self, coin_type='haven', timestamps=np.nan):
        if coin_type=='haven':
            return self.get_supply(self.haven_coin_type,timestamps)
        else:
            pass

    def get_exchange_rate(self, coin_type, coin_type_base='haven', timestamps=np.nan):
        if coin_type_base=='haven':
            return self.get_exchange_rate(coin_type,self.haven_coin_type,timestamps)
        else:
            pass

    # Price is a special case of price history (period = 1m, n_periods = 1)
    # Last valid value logic addresses price or price history accordingly
    def get_price_wip(self, coin_type):
        # Returns [$]
        price = self.price_history(haven_coin, '1m', 1)
        self.last_valid_price = price
        return price

    def get_price_history_wip(self, coin_type, period, n_periods):
        # gets price history
        # Returns [$]
        BIsHaven = (self.name == haven_coin.name)
        BIsSinglePrice = (period == '1m') and (n_periods == 1)

        # Get Haven Price History [$/Haven]
        if BIsHaven:
            # Price fetched from exchange will already be USD, therefore conversion factor is 1
            haven_to_usd = 1
        elif BIsSinglePrice:
            haven_to_usd = haven_coin.last_valid_price
        else:
            haven_to_usd = haven_coin.last_valid_price_history

        # Get Price History [Haven/Coin], for a given exchange
        if BIsHaven:
            coin_pair = haven_coin.name + '/USD'
        else:
            coin_pair = self.name + '/' + haven_coin.name

        try:
            # Get OHLCV in Haven per Coin
            # Last element is most recent (??)
            all_OHLCV = self.exchange.fetch_ohlcv(coin_pair, period)
            # Get V (closing value), still in Haven per Coin
            selected_OHLCV = np.asarray(all_OHLCV[-n_periods:], 'float')
            # Price [$] = Haven x Haven Price, elementwise
            price_history = np.multiply(selected_OHLCV[:, -2], haven_to_usd)
            # Store Price history if not single value
            if BIsSinglePrice:
                price_history = np.asscalar(price_history)
            else:
                self.last_valid_price_history = price_history
            return price_history
        except:
            if BIsSinglePrice:
                return self.last_valid_price
            else:
                return self.last_valid_price_history

    def get_supply_wip(self, coin_type):
        # gets supply - will have to query coinmarketcap for this one
        # only coinmarketcap has the total supply
        try:
            ticker = ccxt.coinmarketcap().fetch_ticker(coin_type + '/USD')
            supply = ticker['info']['available_supply']
            self.coinstats.set_last_valid_supply(coin_type, supply)
        except:
            supply = self.coinstats.get_last_valid_supply(coin_type)

        return supply

    def get_exchange_rate_wip(self, coin_type, coin_type_base):
        pass

    def get_exchange_rate_history_wip(sel, coin_type, coin_type_base):
        pass
