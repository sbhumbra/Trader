import numpy as np
import time
import ccxt
from scipy.interpolate import interp1d


class Exchange:
    def __init__(self, marketplace=ccxt.binance(), haven_marketplace=ccxt.bitfinex(),
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

    def get_price(self, timestamp_start, coin_type='haven', timestamp_end=np.nan):
        # timestamp mandatory and in seconds
        # timestamp_end used to get price history in range [timestamp, timestamp_end]
        if coin_type == 'haven':
            return self.get_price(timestamp_start, self.haven_coin_type, timestamp_end)
        elif coin_type == 'EUR':
            return 1

        if np.isnan(timestamp_end):
            print('Getting price at time: ' + str(timestamp_start))
        else:
            print('Getting prices between time ' + str(timestamp_start) + ' and time ' + str(timestamp_end))

        exchange_rate = self.get_exchange_rate(timestamp_start, coin_type=coin_type, timestamp_end=timestamp_end)
        if self.haven_coin_type == 'USDT':
            fiat_exchange_rate = self.dollar_to_euro
        else:
            fiat_exchange_rate = self.dollar_to_euro * self.get_exchange_rate(timestamp_start,
                                                                              coin_type=self.haven_coin_type,
                                                                              coin_type_base='USD',
                                                                              timestamp_end=timestamp_end)  # shortcut for haven
        price = np.multiply(exchange_rate, fiat_exchange_rate)
        if np.isscalar(price):
            print('Price: ' + str(price))
            print('')

        return price

    def get_exchange_rate(self, timestamp_start, coin_type='haven', coin_type_base='haven', marketplace=None,
                          timestamp_end=np.nan):
        coin_pair = coin_type + '/' + coin_type_base
        if coin_type == coin_type_base:
            if not coin_type == self.haven_coin_type:
                print('WARNING: Getting exchange rate for pair: ' + coin_pair)
            return 1
        elif coin_type == 'haven':
            return self.get_exchange_rate(timestamp_start, self.haven_coin_type, 'USD', self.haven_marketplace,
                                          timestamp_end)
        elif coin_type_base == 'haven':
            return self.get_exchange_rate(timestamp_start, coin_type, self.haven_coin_type, self.marketplace,
                                          timestamp_end)
        else:
            print('Getting exchange rate: ' + coin_pair)
            if not marketplace:
                marketplace = self.marketplace

            flag_complete = False
            query_counter = 0

            while not flag_complete:
                try:
                    # Make sure we go at least three minutes so that we get at least two data points
                    query_time = int(timestamp_start - (180*1)) * 1000

                    # All candles at one minute resolution since query time
                    candles = marketplace.fetch_ohlcv(coin_pair, '1m', query_time)
                    candles = np.asarray(candles)
                    timestamps = candles[:, 0] / 1000
                    timestamp_min = np.min(timestamps)
                    exchange_rates = candles[:, 4]

                    if np.isnan(timestamp_end):
                        # Linear interpolate to get exchange rate, clipping if necessary
                        bounds = (exchange_rates[0], exchange_rates[-1])
                        f = interp1d(timestamps, exchange_rates, bounds_error=False,
                                     fill_value=bounds)  # will error if we only have one data point
                        exchange_rate = np.asscalar(f(timestamp_start))
                    else:
                        # We want to return all exchange rates between timestamp_start and timestamp_end
                        flag_in_range = np.logical_and(np.greater_equal(timestamps, timestamp_start),
                                                       np.less_equal(timestamps, timestamp_end))
                        exchange_rate = np.asarray(exchange_rates[flag_in_range])

                    flag_complete = True
                    # pythonic way of testing if a variable is a scalar
                    if np.isscalar(exchange_rate):
                        print('Exchange rate: ' + str(exchange_rate))
                    return exchange_rate
                except:
                    query_counter += 1
                    if query_counter == self.num_exchange_query_tolerance:
                        print('ERROR: max exchange query attempts reached!!!')
                        raise
                    print('WARNING: exchange query failed, re-attempting')
                    time.sleep(1)

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
