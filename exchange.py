import time

import ccxt
import numpy as np
from scipy.interpolate import interp1d


class Exchange:
    def __init__(self, marketplace=ccxt.binance(), haven_marketplace=ccxt.bitfinex(),
                 haven_coin_type='USDT'):

        self.df_transaction_format = {'transaction_id': [], 'coin_pair': [], 'transaction_amount': [],
                                      'transaction_type': []}

        #   Get coin-coin exchange rates from this marketplace (e.g. binance)
        self.marketplace = marketplace
        self.marketplace.load_markets(True)

        #   Get haven-dollar exchange rate from this marketplace (e.g. bitfinex)
        self.haven_marketplace = haven_marketplace
        self.haven_coin_type = haven_coin_type

        #   Sad Luca
        self.dollar_to_euro = 0.81

        #   If the exchange doesn't return a price, we wait and query again this many times before giving up.
        self.num_exchange_query_tolerance = 5

    def place_order(self, df_transaction, price=np.nan):
        # place order, then update transaction_id.
        # price to be used if we don't want market rate and instead want to place a limit order
        num_transactions = len(df_transaction.index)
        if np.isnan(price):
            for idx in range(0, num_transactions):
                coin_pair = df_transaction.at[idx, 'coin_pair']
                flag_sell = df_transaction.at[idx, 'transaction_type'] == 'sell'
                amount = df_transaction.at[idx, 'transaction_amount']
                coin_pair_limits = self.marketplace.markets[coin_pair]['limits']
                coin_pair_resolution = self.marketplace.markets[coin_pair]['lot']
                amount = np.maximum(coin_pair_limits['amount']['min'], amount)
                amount = np.floor(amount / coin_pair_resolution) * coin_pair_resolution

                if flag_sell:
                    print('Pair: ' + coin_pair + ' ; Selling: ' + str(amount))
                    out = self.marketplace.create_market_sell_order(coin_pair, amount)
                    df_transaction.at[idx, 'transaction_id'] = out['id']
                    # correct amount to what was actually traded
                    df_transaction.at[idx, 'transaction_amount'] = amount
                else:
                    print('Pair: ' + coin_pair + ' ; Buying: ' + str(amount))
                    number_attempts = 0
                    while number_attempts < self.num_exchange_query_tolerance:
                        try:
                            out = self.marketplace.create_market_buy_order(coin_pair, amount)
                            df_transaction.at[idx, 'transaction_id'] = out['id']
                            # correct amount to what was actually traded
                            df_transaction.at[idx, 'transaction_amount'] = amount
                            break
                        except ccxt.errors.InsufficientFunds:
                            print('Insufficient funds - retrying with lower buy amount')
                            number_attempts += 1
                            # we tried to buy too many coins - try to get fewer
                            amount *= 0.95
                            amount = np.maximum(coin_pair_limits['amount']['min'], amount)
                            amount = np.floor(amount / coin_pair_resolution) * coin_pair_resolution
            return
        else:
            raise Exception("Limit orders unsupported")

    def query_order(self, df_transaction):
        # This time we must have the id - it checks the status of the transaction on the marketplace.
        # df_transaction is a dataframe and can contain many orders; it is passed as reference
        # Don't query an order if it has already been completed
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

        # if np.isnan(timestamp_end):
        # print('Getting price at time: ' + str(timestamp_start))
        # else:
        # print('Getting prices between time ' + str(timestamp_start) + ' and time ' + str(timestamp_end))

        exchange_rate = self.get_exchange_rate(timestamp_start, coin_type=coin_type, timestamp_end=timestamp_end)
        if self.haven_coin_type == 'USDT':
            fiat_exchange_rate = self.dollar_to_euro
        else:
            fiat_exchange_rate = self.dollar_to_euro * self.get_exchange_rate(timestamp_start,
                                                                              coin_type=self.haven_coin_type,
                                                                              coin_type_base='USD',
                                                                              timestamp_end=timestamp_end)
        price = np.multiply(exchange_rate, fiat_exchange_rate)

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
            if not marketplace:
                marketplace = self.marketplace

            flag_complete = False
            query_counter = 0

            while not flag_complete:
                try:
                    # Make sure we go at least three minutes so that we get at least two data points
                    query_time = int(timestamp_start - (180 * 1)) * 1000

                    # All candles at one minute resolution since query time
                    candles = marketplace.fetch_ohlcv(coin_pair, '1m', query_time)
                    candles = np.asarray(candles)
                    timestamps = candles[:, 0] / 1000
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
                    return exchange_rate
                except:
                    query_counter += 1
                    if query_counter == self.num_exchange_query_tolerance:
                        print('ERROR: max exchange query attempts reached!!!')
                        raise
                    print('WARNING: exchange query failed, re-attempting')
                    time.sleep(1)

    def value_coin_holding(self, timestamp, coin_type):
        num_coins = self.num_coin_holding(coin_type)
        price_per_coin = self.get_price(timestamp, coin_type)
        return num_coins * price_per_coin

    def value_portfolio(self, timestamp, portfolio):
        portfolio.current_liquid_funds = self.get_liquid_funds(timestamp)
        num_attempts = 0
        while num_attempts < self.num_exchange_query_tolerance:
            try:
                balance = self.marketplace.fetch_balance()
                balance = balance['free']
                coins_held = [[coin_type, balance[coin_type]] for coin_type in balance if
                              balance[coin_type] > 0 and not coin_type == 'GAS' and not coin_type == 'ONT']
                total_value_held = 0
                while coins_held:
                    # Remove coin from the list (while loop ends at empty list)
                    coin_held = coins_held.pop()
                    coin_type_held = coin_held[0]
                    num_coin_held = coin_held[1]
                    value_coin_held = self.value_coin_holding(timestamp, coin_type_held)
                    total_value_held += value_coin_held
                    portfolio.current_holdings[coin_type_held] = {'num': num_coin_held, 'val': value_coin_held}

                print('Current portfolio value: ' + "{:.2f}".format(total_value_held) + ' euros')
                return total_value_held
            except:
                num_attempts += 1

        raise Exception("ERROR: Unable to value portfolio!")

    def num_coin_holding(self, coin_type):
        # net of buffer we need to keep
        num_attempts = 0
        while num_attempts < self.num_exchange_query_tolerance:
            try:
                balance = self.marketplace.fetch_balance()
                coin_balance = balance[coin_type]['free']
                if coin_type == 'USDT':
                    # for the pairs I've seen we need to round down to the nearest cent
                    # not generic for other havens
                    coin_resolution = 0.01
                    coin_balance = np.floor(coin_balance / coin_resolution) * coin_resolution
                else:
                    coin_pair = coin_type + '/' + self.haven_coin_type
                    coin_max_limit = self.marketplace.markets[coin_pair]['limits']['amount']['max']
                    coin_resolution = self.marketplace.markets[coin_pair]['lot']
                    coin_balance = np.minimum(coin_balance, coin_max_limit)
                    coin_balance = np.floor(coin_balance / coin_resolution) * coin_resolution

                return coin_balance
            except:
                num_attempts += 1

        print('ERROR: Unable to get number of ' + coin_type + ' from exchange')
        return 0

    def get_liquid_funds(self, timestamp):
        total_liquid_funds = self.value_coin_holding(timestamp, self.haven_coin_type)
        print('Total liquid funds (Haven/EUR): ' + str(total_liquid_funds))
        return total_liquid_funds
