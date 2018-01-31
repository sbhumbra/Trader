import numpy as np
import time
import pandas as pd
import ccxt


class Exchange:
    def __init__(self, coin_types, marketplace=ccxt.binance(), haven_marketplace=ccxt.bitfinex(),
                 haven_coin_type='USDT'):

        self.df_transaction_format = {'transaction_id': [], 'coin_pair': [], 'transaction_amount': [],
                                      'transaction_type': []}

        #   Get coin-coin exchange rates from this marketplace (e.g. binance)
        self.marketplace = marketplace

        #   Get haven-dollar exchange rate from this marketplace (e.g. bitfinex)
        self.haven_marketplace = haven_marketplace
        self.haven_coin_type = haven_coin_type

        #   Sad Luca
        self.dollar_to_euro = 0.81

        #   If the exchange doesn't return a price, we wait and query again this many times before giving up.
        #   Every query attempt, we iterate backwards in time to have more chance of getting a price
        self.num_exchange_query_tolerance = 5

        # trades = binance.fetch_my_trades('BTC/USDT') - get transaction
        # markets = binance.fetch_markets() - get coin types

    def place_order(self, df_transaction, price=np.nan):
        # place order, then update transaction_id.
        # num_coin_bought and time_completed will still be empty
        # price to be used if we don't want market rate and instead want to place a limit order
        num_transactions = len(df_transaction.index)
        if np.isnan(price):
            for idx in range(0, num_transactions):
                coin_pair = df_transaction.at[idx, 'coin_pair']
                flag_sell = df_transaction.at[idx, 'transaction_type'] == 'sell'
                amount = df_transaction.at[idx, 'transaction_amount']
                if flag_sell:
                    print('Pair: ' + coin_pair + ' ; Selling: ' + str(amount))
                    out = self.marketplace.create_market_sell_order(coin_pair, amount)
                else:
                    print('Pair: ' + coin_pair + ' ; Buying: ' + str(amount))
                    out = self.marketplace.create_market_buy_order(coin_pair, amount)
                df_transaction.at[idx, 'transaction_id'] = out['id']

            print('')
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

        for idx in range(0, num_transactions):
            if not flag_all_orders_completed[idx]:
                coin_pair = df_transaction.at[idx, 'coin_pair']
                transaction_id = df_transaction.at[idx, 'transaction_id']
                order = self.marketplace.fetch_order(transaction_id, symbol=coin_pair)
                if order['status'] == 'closed':
                    flag_all_orders_completed[idx] = True
        return all(flag_all_orders_completed)

    def cancel_order(self, df_transaction):
        # cancel incomplete orders
        id_transactions_to_cancel = []
        num_transactions = len(df_transaction.index)
        for idx in range(0, num_transactions):
            coin_pair = df_transaction.at[idx, 'coin_pair']
            transaction_id = df_transaction.at[idx, 'transaction_id']
            order = self.marketplace.fetch_order(transaction_id, symbol=coin_pair)
            if order['status'] == 'open':
                self.marketplace.cancel_order(transaction_id, symbol=coin_pair)
                id_transactions_to_cancel.append(idx)

        df_transaction.drop(df_transaction.index[id_transactions_to_cancel], inplace=True)

    def get_price(self, timestamp, coin_type='haven'):
        # time mandatory and in seconds
        if coin_type == 'haven':
            return self.get_price(timestamp, self.haven_coin_type)
        elif coin_type == 'EUR':
            return 1

        print('Getting price at time: ' + str(timestamp))
        exchange_rate = self.get_exchange_rate(timestamp, coin_type=coin_type)
        if self.haven_coin_type == 'USDT':
            fiat_exchange_rate = self.dollar_to_euro
        else:
            fiat_exchange_rate = self.dollar_to_euro * self.get_exchange_rate(timestamp,
                                                                              coin_type=self.haven_coin_type,
                                                                              coin_type_base='USD')  # shortcut for haven
        price = exchange_rate * fiat_exchange_rate
        print('Price: ' + str(price))
        print('')
        return price

    def get_exchange_rate(self, timestamp, coin_type='haven', coin_type_base='haven', marketplace=None):
        coin_pair = coin_type + '/' + coin_type_base
        if coin_type == coin_type_base:
            if not coin_type == self.haven_coin_type:
                print('WARNING: Check exchange rate? Pair: ' + coin_pair)
            return 1
        elif coin_type == 'haven':
            return self.get_exchange_rate(timestamp, self.haven_coin_type, 'USD', self.haven_marketplace)
        elif coin_type_base == 'haven':
            return self.get_exchange_rate(timestamp, coin_type, self.haven_coin_type, self.marketplace)
        else:
            print('Getting exchange rate: ' + coin_pair)
            if not marketplace:
                marketplace = self.marketplace

            flag_complete = False
            query_offset = 1  # minut3

            while not flag_complete:
                try:
                    # Make sure we go a minute in the past to get a value
                    query_time = int(timestamp - (60 * query_offset)) * 1000

                    candles = marketplace.fetch_ohlcv(coin_pair, '1m', query_time)
                    exchange_rate = candles[0][4]

                    flag_complete = True
                    print('Exchange rate: ' + str(exchange_rate))
                    return exchange_rate
                except:
                    if query_offset == self.num_exchange_query_tolerance:
                        print('ERROR: max exchange query attempts reached!!!')
                        raise
                    query_offset += 1
                    print('WARNING: exchange query failed, re-attempting')
                    print('Getting price ' + str(query_offset) + ' minutes earlier')
                    time.sleep(2)

    def value_coin_holding(self, coin_type):
        now = int(time.time())
        num_coins = self.num_coin_holding(coin_type)
        price_per_coin = self.get_price(now, coin_type)
        return num_coins * price_per_coin

    def num_coin_holding(self, coin_type):
        num_attempts = 0
        while num_attempts < self.num_exchange_query_tolerance:
            try:
                balance = self.marketplace.fetch_balance()
                return balance[coin_type]['free']
            except:
                num_attempts += 1

        print('ERROR: num_coin_holding ; unable to get value from exchange')
        return 0

    def get_liquid_funds(self):
        total_liquid_funds = self.value_coin_holding(self.haven_coin_type)
        print('Total liquid funds (Haven/EUR): ' + str(total_liquid_funds))
        return total_liquid_funds
