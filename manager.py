import time

import ccxt
import numpy as np
import pandas as pd
import scipy.io as sio

import exchange as E
import fake_exchange as FE
import forecaster as F
import portfolio as P
import coin as C


class Manager:
    def __init__(self, timestamp, flag_fake_exchange=False,
                 available_coin_types=['BTC', 'ETH', 'BNB', 'LTC', 'NEO']):
        # Coin info
        self.list_of_coin_types = []
        self.coin_ids = []
        self.coins = {}
        self.set_available_coin_types(available_coin_types)

        binance = ccxt.binance()
        mat_file = sio.loadmat("api_things.mat")
        binance.apiKey = mat_file['api_key'][0]
        binance.secret = mat_file["api_secret"][0]

        # robust wrapper for placing / querying / cancelling orders & getting prices
        if flag_fake_exchange:
            self.exchange = FE.FakeExchange(timestamp, marketplace=binance,
                                            haven_marketplace=ccxt.bitfinex())  # Default haven = USDT
        else:
            self.exchange = E.Exchange(marketplace=binance, haven_marketplace=ccxt.bitfinex())  # Default haven = USDT

        # thresholds (euros) at which to buy / sell, and the value (euros) of the order if buying
        self.threshold_buy_ratio = 0.5  # percent expected
        self.threshold_buy_ratio_2 = 2
        self.threshold_sell_ratio = -0.5  # percent expected (-ive for loss) - sell at low gain to pre-empt fall
        self.threshold_sell_ratio_2 = -2
        self.buy_value = 5  # euros
        self.prediction_time = 15 * 60  # seconds
        self.backsampling_time = 15 * 60  # seconds

        # for predicting future prices / exchange rates
        self.forecaster = F.Forecaster(self.exchange, self.backsampling_time)

        # for working out how well we're doing
        self.portfolio = P.Portfolio(timestamp, self.exchange)

    def trade(self, timestamp):
        # get current timestamp and get future timestamp for prediction
        now = timestamp  # for Luca
        future_time = now + self.prediction_time
        past_time = now - self.backsampling_time

        # Update all coin info: amount held, current price, future price, past gradient...
        self.check_coins(now, future_time, past_time)

        # Decide which coins to sell and which to buy
        # Lists are in descending priority order
        (coins_to_sell, coins_to_buy) = self.choose_trades()

        flag_any_sells = len(coins_to_sell) > 0
        flag_any_buys = len(coins_to_buy) > 0

        if flag_any_sells:
            print("Selling coinage...")
            print('')
            # Calculate amounts to sell, create orders and execute
            self.set_sell_amounts(coins_to_sell)
            transactions_to_make = self.list_transactions_to_make(coins_to_sell, 'sell')
            self.manage_orders(df_transactions_to_make=transactions_to_make, timeout=60)

        # How much haven have we got?
        total_liquid_funds = self.exchange.get_liquid_funds(now)

        if flag_any_buys and np.greater(total_liquid_funds, 0):
            print("Buying coinage...")
            print('')
            # Calculate amounts to buy, create orders and execute
            # If we run out of money while making buy orders then
            # some coins won't have a buy amount associated with them; we take
            # only the ones that do.
            self.set_buy_amounts(coins_to_buy, total_liquid_funds, now)
            coins_to_buy = [c for c in coins_to_buy if len(c) == 2]
            transactions_to_make = self.list_transactions_to_make(coins_to_buy, 'buy')
            self.manage_orders(df_transactions_to_make=transactions_to_make, timeout=60)

        # Update all coin plots
        self.update_coin_plots(timestamp)

        # return True if any trade
        return flag_any_sells or flag_any_buys

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

    def list_transactions_to_make(self, coins_to_trade, transaction_type):
        transactions_to_make = pd.DataFrame(self.exchange.df_transaction_format)

        for coin_trade in coins_to_trade:
            coin_type = coin_trade[0]
            transaction_amount = coin_trade[1]
            coin_pair = coin_type + '/' + self.exchange.haven_coin_type
            transaction_to_make = pd.DataFrame(
                data=[[coin_pair, transaction_amount, transaction_type]],
                columns=['coin_pair', 'transaction_amount', 'transaction_type'])
            # concat will set nan all unpopulated df values .e.g ID
            transactions_to_make = pd.concat([transactions_to_make, transaction_to_make], ignore_index=True)
        return transactions_to_make

    def calculate_return(self, timestamp):
        self.portfolio.calculate_return(timestamp, self.exchange)
        # Update portfolio plot
        self.update_portfolio_plot()

    def check_coins(self, now_timestamp, future_timestamp, past_timestamp):
        # For each coin:
        #   Get current price and number held
        #   Forecast future price, calculating current price gradient
        #   Calculate past price gradient
        for coin_type in self.list_of_coin_types:
            c = self.coins[coin_type]  # for reference
            c.update_num_coin_held(self.exchange)
            c.update_current_price(self.exchange, now_timestamp)
            c.forecast_future_price(self.forecaster, now_timestamp, future_timestamp)
            c.calculate_past_price_gradient(self.exchange, past_timestamp, self.backsampling_time)
            print("Current price of " + coin_type + " is " + str(c.current_price))
            print("Last change: " + str(c.past_price_ratio) + \
                  " % ; Predicted change: " + str(c.current_price_ratio) + " %")
            print("")

    def choose_trades(self):
        # Return two lists of coin_types, one to sell and the other to buy
        # Lists are sorted in descending priority order
        coins_to_sell = []
        coins_to_buy = []

        for coin_type in self.list_of_coin_types:
            c = self.coins[coin_type]
            change_in_gradient = c.current_price_ratio - c.past_price_ratio

            # SELL anything that's performing worse than threshold and that we own enough of
            flag_loss = np.logical_or(
                np.less(change_in_gradient, self.threshold_sell_ratio),
                np.less(c.current_price_ratio, self.threshold_sell_ratio_2))
            flag_have_coin = np.greater(c.num_coin_held, 0)
            if np.logical_and(flag_loss, flag_have_coin):
                # No priorities here
                coins_to_sell.append(coin_type)  # no priorities here
                continue

            # BUY anything that's performing better than threshold
            flag_gain = np.logical_or(
                np.greater(change_in_gradient, self.threshold_buy_ratio),
                np.greater(c.current_price_ratio, self.threshold_buy_ratio_2))
            if flag_gain:
                # We want to sort by price gradient, so add this to the list for now
                coins_to_buy.append((coin_type, c.current_price_ratio))

        # This sorts coins_to_buy by numerical data (price gradient) in ascending order
        coins_to_buy.sort()
        # ... and now descending order
        coins_to_buy.reverse()
        # ... and now take only the coin_type
        coins_to_buy = [c[0] for c in coins_to_buy]

        return coins_to_sell, coins_to_buy

    def set_sell_amounts(self, coins_to_sell):
        # coins_to_sell modified by reference
        # TODO: calculate amounts to sell instead of selling all?
        for idx, coin_type in enumerate(coins_to_sell):
            coins_to_sell[idx] = (coin_type, self.coins[coin_type].num_coin_held)

    def set_buy_amounts(self, coins_to_buy, total_liquid_funds, now_timestamp):
        # coins_to_buy modified by reference
        for idx, coin_type in enumerate(coins_to_buy):
            funds_to_spend = np.minimum(self.buy_value, total_liquid_funds)
            buy_amount = funds_to_spend / self.coins[coin_type].current_price
            coins_to_buy[idx] = (coin_type, buy_amount)
            total_liquid_funds -= funds_to_spend
            print('Buying ' + str(buy_amount) + ' ' + coin_type + ' for expected '
                  + str(self.coins[coin_type].current_price_ratio) + ' % gainz')
            if total_liquid_funds <= 0:
                break

    def update_coin_plots(self, timestamp):
        for coin_type in self.list_of_coin_types:
            c = self.coins[coin_type]
            c.update_plot(self.exchange, timestamp)

    def update_portfolio_plot(self):
        pass

    def set_available_coin_types(self, available_coin_types):
        self.list_of_coin_types = available_coin_types
        num_coin_types = len(self.list_of_coin_types)
        self.coin_ids = (np.linspace(1, num_coin_types, num_coin_types) - 1).astype('int')

        self.coins = {}
        for coin_type in self.list_of_coin_types:
            self.coins[coin_type] = C.Coin(coin_type)
