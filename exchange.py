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
            num_transactions = len(df_transaction.index)
            if np.isnan(price):
                for idx in range(0, num_transactions):
                    to_buy = df_transaction.at[idx, 'coin_type_bought']
                    to_sell = df_transaction.at[idx, 'coin_type_sold']
                    amount_to_sell = df_transaction.at[idx, 'num_coin_sold']
                    print('Buying' + to_buy + 'for' + amount_to_sell + ' ' + to_sell)
                    if to_buy == self.haven_coin_type:
                        out = self.marketplace.create_market_sell_order(
                            to_sell + '/' + to_buy,
                            amount_to_sell)
                    else:
                        out = self.marketplace.create_market_buy_order(
                            to_buy + '/' + to_sell,
                            amount_to_sell)
                    df_transaction.at[idx, 'transaction_id'] = out['id']
            else:
                raise Exception("Limit orders unsupported")

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
                if not flag_all_orders_completed[idx]:
                    coin_sell_price = (1 - self.sell_fee) * self.get_price(df_transaction.at[idx, 'coin_type_sold'])
                    coin_buy_price = (1 + self.buy_fee) * self.get_price(df_transaction.at[idx, 'coin_type_bought'])
                    exchange_rate = coin_sell_price / coin_buy_price  # ($/H) / ($/B) -> B/H
                    num_coin_bought = exchange_rate * df_transaction.at[idx, 'num_coin_sold']
                    df_transaction.at[idx, 'num_coin_bought'] = num_coin_bought
                    df_transaction.at[idx, 'time_completed'] = int(time.time())
                    flag_all_orders_completed[idx] = True
        else:
            for idx in range(0, num_transactions):
                if not flag_all_orders_completed[idx]:
                    order = self.marketplace.fetch_order(df_transaction.at[idx, 'transaction_id'])
                    if order['status'] == 'closed':
                        df_transaction.at[idx, 'num_coin_bought'] = order['amount']
                        df_transaction.at[idx, 'time_completed'] = int(order['timestamp'] / 1000)
                        flag_all_orders_completed[idx] = True

        return all(flag_all_orders_completed)

    def cancel_order(self, df_transaction):
        # cancel incomplete orders
        if self.flag_fake_exchange:
            id_transactions_to_cancel = []
            num_transactions = len(df_transaction.index)
            for idx in range(0, num_transactions):
                if np.isnan(df_transaction.at[idx, 'time_completed']):
                    id_transactions_to_cancel.append(idx)

            df_transaction.drop(df_transaction.index[id_transactions_to_cancel], inplace=True)
        else:
            id_transactions_to_cancel = []
            num_transactions = len(df_transaction.index)
            for idx in range(0, num_transactions):
                order = self.marketplace.fetch_order(df_transaction.at[idx, 'transaction_id'])
                if order['status'] == 'open':
                    self.marketplace.cancel_order(df_transaction.at[idx, 'transaction_id'])
                    id_transactions_to_cancel.append(idx)

            df_transaction.drop(df_transaction.index[id_transactions_to_cancel], inplace=True)

    def get_price(self, coin_type='haven', timestamps=np.nan):
        if coin_type == 'haven':
            return self.get_price(self.haven_coin_type, timestamps)
        elif coin_type == 'EUR':
            return 1
        else:
            flag_query_now = np.isnan(timestamps)
            try:
                exchange_rate = self.get_exchange_rate(coin_type=coin_type, timestamps=timestamps)
                if self.haven_coin_type == 'USDT':
                    fiat_exchange_rate = 0.81
                else:
                    fiat_exchange_rate = self.get_exchange_rate(timestamps=timestamps) # shortcut for haven
                price = exchange_rate * fiat_exchange_rate
                if flag_query_now:
                    self.coinstats.set_last_valid_supply(coin_type, price, int(time.time()))
                else:
                    self.coinstats.set_last_valid_supply(coin_type, price, int(timestamps / 1000))
            except:
                [last_valid_price, last_valid_timestamp] = self.coinstats.get_last_valid_price(coin_type)
                if flag_query_now:
                    query_time_delta = np.abs(last_valid_timestamp - int(time.time()))
                    flag_query_valid = query_time_delta <= self.price_time_query_tolerance
                else:
                    query_time_delta = np.abs(last_valid_timestamp - timestamps)
                    flag_query_valid = all(query_time_delta <= self.price_time_query_tolerance)

                if flag_query_valid:
                    price = last_valid_price
                else:
                    price = np.nan
        return price

    def get_supply(self, coin_type='haven', timestamps=np.nan):
        if coin_type == 'haven':
            return self.get_supply(self.haven_coin_type, timestamps)
        else:
            flag_query_now = np.isnan(timestamps)
            try:
                ticker = ccxt.coinmarketcap().fetch_ticker(coin_type + '/USD')
                supply = ticker['info']['available_supply']
                if flag_query_now:
                    self.coinstats.set_last_valid_supply(coin_type, supply, int(time.time()))
                else:
                    self.coinstats.set_last_valid_supply(coin_type, supply, int(timestamps / 1000))
            except:
                [last_valid_supply, last_valid_timestamp] = self.coinstats.get_last_valid_supply(coin_type)
                if flag_query_now:
                    query_time_delta = np.abs(last_valid_timestamp - int(time.time()))
                    flag_query_valid = query_time_delta <= self.supply_time_query_tolerance
                else:
                    query_time_delta = np.abs(last_valid_timestamp - timestamps)
                    flag_query_valid = all(query_time_delta <= self.supply_time_query_tolerance)
                if flag_query_valid:
                    supply = last_valid_supply
                else:
                    supply = np.nan
        return supply

    def get_exchange_rate(self, coin_type='haven', coin_type_base='haven', timestamps=np.nan, marketplace=np.nan):
        if (coin_type == 'haven') or (coin_type == self.haven_coin_type):
            return self.get_exchange_rate(self.haven_coin_type, 'EUR', timestamps, self.haven_marketplace)
        elif coin_type_base == 'haven':
            return self.get_exchange_rate(coin_type, self.haven_coin_type, timestamps, self.marketplace)
        else:
            coin_pair = coin_type + '/' + coin_type_base
            if np.isnan(marketplace):
                marketplace = self.marketplace

            if np.isnan(timestamps):
                # get last exchange rate
                query_time = int((int(time.time()) - 60 * 1) * 1000)
            else:
                query_time = int(timestamps * 1000)

            candles = marketplace.fetch_ohlcv(coin_pair, '1m', query_time)
            exchange_rate = candles[0][4]

            return exchange_rate
