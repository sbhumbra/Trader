import time

import ccxt
import numpy as np
import pandas as pd
import scipy.io as sio

import exchange as E
import forecaster as F
import portfolio as P


class Manager:
    def __init__(self, filename_coinstats='', filename_portfolio=''):
        # Exchange abstracts conversions so these coins need not go directly to Haven (USDT)
        # coins tradeable with USDT on binance
        self.list_of_coin_types = ['BTC', 'ETH', 'BNB', 'LTC', 'NEO']

        # haven coin: USDT for safety
        self.haven_coin_type = 'USDT'

        binance = ccxt.binance()
        mat_file = sio.loadmat("api_things.mat")
        binance.apiKey = mat_file['api_key']
        binance.secret = mat_file["api_secret"]

        # robust wrapper for placing / querying / cancelling orders & getting prices
        self.exchange = E.Exchange(coin_types=self.list_of_coin_types, marketplace=binance,
                                   haven_marketplace=ccxt.bitfinex(), buy_fee=0.01 / 100,
                                   sell_fee=0.01 / 100, haven_coin_type=self.haven_coin_type,
                                   filename_coinstats=filename_coinstats,
                                   flag_fake_exchange=False)  # FAKE EXCHANGE -- CHANGE HERE !!

        # portfolio contains list of completed transactions
        self.portfolio = P.Portfolio(self.exchange, filename_portfolio)

        # for predicting future prices / exchange rates
        self.forecaster = F.Forecaster(self.exchange)

        # thresholds (euros) at which to buy / sell, and the value (euros) of the order if buying
        self.threshold_buy = 5  # euros
        self.threshold_sell = 5  # euros
        self.buy_value = 5  # euros

        # liquidation flag
        num_coin_types = len(self.list_of_coin_types)
        self.flag_liquidate_coin = np.full(num_coin_types, False)

    def trade(self):
        # get current timestamp and get future timestamp for prediction
        now = int(time.time())
        future_time = now + 60 * 10

        # instantiate containers for current / future values
        num_coin_types = len(self.list_of_coin_types)
        coin_ids = (np.linspace(1, num_coin_types, num_coin_types) - 1).astype('int')
        future_values = np.full(num_coin_types, np.nan)
        current_values = np.full(num_coin_types, np.nan)

        # If not liquidating, loop through all coins and calc current / future values
        if not any(self.flag_liquidate_coin):
            for idx, coin_type in enumerate(self.list_of_coin_types):
                future_values[idx] = self.portfolio.num_coin_holding(coin_type) * self.forecaster.forecast(coin_type,
                                                                                                           future_time)
                current_values[idx] = self.portfolio.value_coin_holding(coin_type)

        # Calc p/l in future
        # This will be NaN if liquidating
        print("Current values are " + str(current_values).strip('[]'))
        print("Future values are " + str(future_values).strip('[]'))
        future_profit_loss = future_values - current_values
        # SELL COINS
        # Selling frees up funds for buying...
        # Sell anything that's negative and over threshold and that we own
        # If liquidating, future_profit_loss will be NaN and the check below will be False for all coins
        # This is good as it stops us making trades unintentionally when liquidating
        flag_loss_expected = np.logical_and(-1 * future_profit_loss >= self.threshold_sell, current_values > 0)

        # Which coins should we sell?
        flag_sell_coin = np.logical_or(flag_loss_expected, self.flag_liquidate_coin)
        if any(flag_sell_coin):
            id_coin_types_to_sell = coin_ids[flag_sell_coin]
            list_of_coin_types_to_sell = self.get_list_of_coin_types(id_coin_types_to_sell)

            # How much of each coin should we sell?
            num_coin_types_to_sell = len(list_of_coin_types_to_sell)
            number_of_coins_to_sell = np.full(num_coin_types_to_sell, np.nan)
            for idx, coin_type in enumerate(list_of_coin_types_to_sell):
                if self.flag_liquidate_coin[idx]:
                    number_of_coins_to_sell[idx] = self.portfolio.num_coin_holding(coin_type)
                else:
                    # TODO: calculate number of coins to sell instead of selling all?
                    number_of_coins_to_sell[idx] = self.portfolio.num_coin_holding(coin_type)

            # "Sell" orders
            transactions_to_make = self.sell_coins(list_of_coin_types_to_sell, number_of_coins_to_sell)

            # Execute "sell" orders
            self.manage_orders(df_transactions_to_make=transactions_to_make, timeout=60)

        # BUY COINS
        print("Buying coinage...")
        # Buy anything positive that's over threshold
        # Again, the check below will be False for each coin if we're liquidating
        flag_profit_expected = future_profit_loss >= self.threshold_buy

        # Which coins should we buy and what will the profit be?
        # Liquidation check is explicit here although unnecessary
        flag_buy_coin = np.logical_and(flag_profit_expected, not any(self.flag_liquidate_coin))
        if any(flag_buy_coin):

            id_coin_types_to_buy = coin_ids[flag_buy_coin]
            future_profit = future_profit_loss[flag_buy_coin]

            print("Buying" + id_coin_types_to_buy + " for expected " + future_profit + " moneys")

            # Order coins from most profit to least profit
            # This sorts in ascending (not optional), therefore -1 for descending
            id_priority = np.argsort(-1 * future_profit)
            id_priority_coin_types_to_buy = id_coin_types_to_buy[id_priority].astype('int')

            # Get ordered list of coins to buy
            list_of_coin_types_to_buy = self.get_list_of_coin_types(id_priority_coin_types_to_buy)

            # How much haven should we sell for each coin?
            # TODO: currently same stake for all
            num_haven_for_buy_value = self.buy_value / self.exchange.get_price(self.haven_coin_type)
            num_coin_types_to_buy = len(list_of_coin_types_to_buy)
            number_of_haven_to_sell = np.full(num_coin_types_to_buy, num_haven_for_buy_value)

            # How much haven have we got?
            total_liquid_funds = self.portfolio.value_coin_holding(self.haven_coin_type)

            # "Buy" orders
            transactions_to_make = self.buy_coins(list_of_coin_types_to_buy, number_of_haven_to_sell,
                                                  total_liquid_funds)

            # Execute "buy" orders
            self.manage_orders(df_transactions_to_make=transactions_to_make, timeout=60)

    def stop_trading(self):
        # stop trading so we can withdraw loads of money
        pass

    def liquidate_portfolio(self, num_attempts=1):
        # Attempt to turn all coins into haven (called manually)
        # num_attempts at liquidation
        # Returns bool True if successful

        # Set liquidation flag true for all coins
        self.flag_liquidate_coin.fill(True)

        # Attempt to liquidate portfolio
        for i in range(0, num_attempts):
            self.trade()

        # Check how much of each coin we have
        # TODO: do we need a threshold on this in case we're left with fractions of holdings?
        num_coin_types = len(self.list_of_coin_types)
        flag_none_held = np.full(num_coin_types, False)
        for idx, coin_type in enumerate(self.list_of_coin_types):
            flag_none_held[idx] = self.portfolio.num_coin_holding(coin_type) == 0

        # Success if we don't hold any coins (apart from haven)
        flag_success = all(flag_none_held)

        # Set liquidation flag to false so we can trade again
        # TODO: do we do this only if successful?
        self.flag_liquidate_coin.fill(False)

        return flag_success

    def liquidate_coin(self, coin_type_to_liquidate, num_attempts=1):
        # Attempt to turn a single coin into haven (called manually)
        # num_attempts at liquidation
        # Returns bool True if successful

        # Set liquidation flag to true for this coin
        for idx, coin_type in enumerate(self.list_of_coin_types):
            self.flag_liquidate_coin[idx] = self.list_of_coin_types[idx] == coin_type_to_liquidate

        # Attempt to liquidate coin
        for i in range(0, num_attempts):
            self.trade()

        # Success if we have no coin left
        # TODO: do we need a threshold on this in case we're left with fractions of holdings?
        flag_success = self.portfolio.num_coin_holding(coin_type_to_liquidate) == 0

        return flag_success

    def manage_orders(self, df_transactions_to_make, timeout):
        # Place orders
        self.exchange.place_order(df_transactions_to_make)

        # Monitor orders, record in portfolio and return if all complete
        orders_completed = 0
        for i in range(1, timeout):
            print(i)
            orders_completed = self.exchange.query_order(df_transactions_to_make)
            time.sleep(1)
            # TODO: cancel if price forecast changes?
            if orders_completed:
                break

        # Cancel orders which have been on the exchange too long
        if not orders_completed:
            self.exchange.cancel_order(df_transactions_to_make)

        # After cancelling expired orders, add completed ones to portfolio
        self.portfolio.record_transaction(df_transactions_to_make)

    def buy_coins(self, coin_types_to_buy, number_of_haven_to_sell, total_liquid_funds):
        # Returns data frame of transactions
        transactions_to_make = pd.DataFrame(self.portfolio.df_transaction_format)

        # Each transaction sells a given number of a haven in exchange for coin_type
        for idx, coin_type in enumerate(coin_types_to_buy):
            if total_liquid_funds >= self.buy_value:
                transaction_to_make = pd.DataFrame(
                    data=[[self.haven_coin_type, number_of_haven_to_sell[idx], coin_type]],
                    columns=['coin_type_sold', 'num_coin_sold', 'coin_type_bought'])
                # concat will set nan all unpopulated df values .e.f ID / time completed
                transactions_to_make = pd.concat([transactions_to_make, transaction_to_make], ignore_index=True)
                total_liquid_funds -= self.buy_value  # can we still afford transactions?
            else:
                break

        return transactions_to_make

    def sell_coins(self, coin_types_to_sell, number_of_coins_to_sell):
        # Returns data frame of transactions
        transactions_to_make = pd.DataFrame(self.portfolio.df_transaction_format)

        # Each transaction sells a given number of a coin type in exchange for haven
        for idx, coin_type in enumerate(coin_types_to_sell):
            transaction_to_make = pd.DataFrame(data=[[coin_type, number_of_coins_to_sell[idx], self.haven_coin_type]],
                                               columns=['coin_type_sold', 'num_coin_sold', 'coin_type_bought'])
            # concat will set nan all unpopulated df values e.g. ID / time completed
            transactions_to_make = pd.concat([transactions_to_make, transaction_to_make], ignore_index=True)

        return transactions_to_make

    def get_list_of_coin_types(self, id_coin_types_to_get):
        list_of_coin_types = [self.list_of_coin_types[i] for i in id_coin_types_to_get]
        return list_of_coin_types
