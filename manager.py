import time

import ccxt
import numpy as np
import pandas as pd
import scipy.io as sio

import exchange as E
import fake_exchange as FE
import forecaster as F


class Manager:
    def __init__(self, flag_fake_exchange=False):
        # Exchange abstracts conversions so these coins need not go directly to Haven (USDT)
        # coins tradeable with USDT on binance
        # can get this from exchange
        self.list_of_coin_types = ['BTC', 'ETH', 'BNB', 'LTC', 'NEO']

        binance = ccxt.binance()
        mat_file = sio.loadmat("api_things.mat")
        binance.apiKey = mat_file['api_key'][0]
        binance.secret = mat_file["api_secret"][0]

        # robust wrapper for placing / querying / cancelling orders & getting prices
        if flag_fake_exchange:
            self.exchange = FE.FakeExchange(marketplace=binance,
                                            haven_marketplace=ccxt.bitfinex())  # Default haven = USDT
        else:
            self.exchange = E.Exchange(marketplace=binance, haven_marketplace=ccxt.bitfinex())  # Default haven = USDT

        # for predicting future prices / exchange rates
        self.forecaster = F.Forecaster(self.exchange)

        # thresholds (euros) at which to buy / sell, and the value (euros) of the order if buying
        self.threshold_buy_ratio = 1  # percent expected gain
        self.threshold_sell_ratio = -2  # percent expected loss
        self.buy_value = 5  # euros

    def trade(self):
        # get current timestamp and get future timestamp for prediction
        now = int(time.time())
        prediction_time = 60 * 60  # seconds
        future_time = now + prediction_time

        # instantiate containers for current / future values
        num_coin_types = len(self.list_of_coin_types)
        coin_ids = (np.linspace(1, num_coin_types, num_coin_types) - 1).astype('int')
        future_prices = np.full(num_coin_types, np.nan)
        current_prices = np.full(num_coin_types, np.nan)
        num_coins_held = np.full(num_coin_types, np.nan)

        # Loop through all coins and calc current / future prices and number held
        for idx, coin_type in enumerate(self.list_of_coin_types):
            future_prices[idx] = self.forecaster.forecast(coin_type, future_time)
            current_prices[idx] = self.exchange.get_price(now, coin_type)
            num_coins_held[idx] = self.exchange.num_coin_holding(coin_type)

        # Calculate price gradient
        print("Coins are " + str(self.list_of_coin_types))
        print("Current prices are " + str(current_prices).strip('[]'))
        print("We think future prices are " + str(future_prices).strip('[]'))
        print('')
        price_gradient = np.asarray(100 * np.divide((future_prices - current_prices), current_prices))  # percent

        # SELL COINS
        # Selling frees up funds for buying...
        # Sell anything that's performing worse than threshold and that we own enough of
        flag_loss = np.less(price_gradient, self.threshold_sell_ratio)
        flag_have_coin = np.greater(num_coins_held, 0)
        flag_sell_coin = np.logical_and(flag_loss, flag_have_coin)

        if any(flag_sell_coin):
            print("Selling coinage...")
            print('')

            id_coin_types_to_sell = coin_ids[flag_sell_coin]
            list_of_coin_types_to_sell = self.get_list_of_coin_types(id_coin_types_to_sell)

            # How much of each coin should we sell?
            num_coin_types_to_sell = len(list_of_coin_types_to_sell)
            number_of_coins_to_sell = np.full(num_coin_types_to_sell, np.nan)
            for idx, coin_type in enumerate(list_of_coin_types_to_sell):
                # TODO: calculate number of coins to sell instead of selling all?
                number_of_coins_to_sell[idx] = self.exchange.num_coin_holding(coin_type)

            # "Sell" orders
            transactions_to_make = self.list_transactions_to_make(list_of_coin_types_to_sell,
                                                                  number_of_coins_to_sell, 'sell')

            # Execute "sell" orders
            self.manage_orders(df_transactions_to_make=transactions_to_make, timeout=60)

        # BUY COINS
        # Buy anything that's performing better than threshold and that we can afford
        flag_gain = np.greater(price_gradient, self.threshold_buy_ratio)

        # How much haven have we got?
        total_liquid_funds = self.exchange.get_liquid_funds()

        flag_have_money_to_spend = np.greater(total_liquid_funds, 0)

        flag_buy_coin = np.logical_and(flag_gain, flag_have_money_to_spend)

        if any(flag_buy_coin):
            print("Buying coinage...")
            print('')

            id_coin_types_to_buy = coin_ids[flag_buy_coin]
            sufficient_price_gradient = price_gradient[flag_buy_coin]

            # Order coins from most profit to least profit
            # This sorts in ascending (not optional), therefore -1 for descending
            id_priority = np.argsort(-1 * sufficient_price_gradient)
            id_priority_coin_types_to_buy = id_coin_types_to_buy[id_priority].astype('int')
            price_gradient_sorted = sufficient_price_gradient[id_priority]

            # Get ordered list of coins to buy
            list_of_coin_types_to_buy = self.get_list_of_coin_types(id_priority_coin_types_to_buy)

            # How much of each coin do we buy?
            num_coin_types_to_buy = len(list_of_coin_types_to_buy)
            num_coin_to_buy = np.full(num_coin_types_to_buy, np.nan)

            for idx, coin_type in enumerate(list_of_coin_types_to_buy):
                funds_to_spend = np.minimum(self.buy_value, total_liquid_funds)
                num_coin_to_buy[idx] = funds_to_spend / self.exchange.get_price(now, coin_type)
                total_liquid_funds -= funds_to_spend
                print('Buying ' + str(num_coin_to_buy[idx]) + ' ' + coin_type + ' for expected profit of '
                      + str(price_gradient_sorted[idx]) + ' percent gainz')
                if total_liquid_funds == 0:
                    break

            id_coins_cannot_afford = np.isnan(num_coin_to_buy)

            num_coin_to_buy = num_coin_to_buy[np.logical_not(id_coins_cannot_afford)]
            list_of_coin_types_to_buy = list_of_coin_types_to_buy[np.logical_not(id_coins_cannot_afford)]

            # "Buy" orders
            transactions_to_make = self.list_transactions_to_make(list_of_coin_types_to_buy,
                                                                  num_coin_to_buy, 'buy')

            # Execute "buy" orders
            self.manage_orders(df_transactions_to_make=transactions_to_make, timeout=60)

    def stop_trading(self):
        # 1) fetch all open orders
        # 2) cancel all open orders
        # 3) compute profit/loss per coin and plot things and buy lambo
        pass

    def manage_orders(self, df_transactions_to_make, timeout):
        # Place orders
        self.exchange.place_order(df_transactions_to_make)

        # Monitor orders and return if all complete
        orders_completed = 0
        for i in range(1, timeout):
            orders_completed = self.exchange.query_order(df_transactions_to_make)
            if orders_completed:
                break

            time.sleep(1)

        # Cancel orders which have been on the exchange too long
        if not orders_completed:
            self.exchange.cancel_order(df_transactions_to_make)

    def list_transactions_to_make(self, coin_types_to_trade, transaction_amounts, transaction_type):

        transactions_to_make = pd.DataFrame(self.exchange.df_transaction_format)

        for idx, coin_type in enumerate(coin_types_to_trade):
            coin_pair = coin_type + '/' + self.exchange.haven_coin_type
            transaction_to_make = pd.DataFrame(
                data=[[coin_pair, transaction_amounts[idx], transaction_type]],
                columns=['coin_pair', 'transaction_amount', 'transaction_type'])
            # concat will set nan all unpopulated df values .e.g ID
            transactions_to_make = pd.concat([transactions_to_make, transaction_to_make], ignore_index=True)
        return transactions_to_make

    def get_list_of_coin_types(self, id_coin_types_to_get):
        list_of_coin_types = [self.list_of_coin_types[i] for i in id_coin_types_to_get]
        return np.array(list_of_coin_types)
