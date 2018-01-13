import ccxt
import time
import numpy as np
import pandas as pd

import coin as c
import exchange as e
import forecaster as f
import portfolio as p


class Manager:
    def __init__(self):
        self.list_of_coin_types = ['BTC', 'USDT', 'BNB', 'BCC', 'LTC', 'NEO']  # coins tradeable with USDT on binance
        self.haven_coin = c.Coin("ETH", ccxt.bitfinex())  # when market tanks, USDT will look good
        self.portfolio = p.Portfolio(self.haven_coin)
        self.forecaster = f.Forecaster(self.haven_coin)  # to be able to go from usdt to real money
        self.exchange = e.Exchange(ccxt.binance(), 0.01 / 100, 0.01 / 100, self.haven_coin)

        self.threshold_buy = 5  # euros
        self.threshold_sell = 5  # euros
        self.buy_value = 5  # euros

    def trade(self):
        # get current timestamp and get future timestamp for prediction
        now = int(time.time())
        future_time = now + 60 * 10

        # instantiate containers for future values and current values
        num_coin_types = len(self.list_of_coin_types)
        coin_ids = np.linspace(1, num_coin_types, num_coin_types).astype('int')
        future_values = np.asarray([np.nan]) * num_coin_types
        current_values = np.asarray([np.nan]) * num_coin_types

        # loop through all coins and calc current value and future value
        for idx, coin_type in enumerate(self.list_of_coin_types):
            future_values[idx] = self.portfolio.num_coin_holding(coin_type) * self.forecaster.forecast(coin_type,
                                                                                                       future_time)
            current_values[idx] = self.portfolio.value_coin_holding(coin_type)

        # calc p/l in future
        future_profit_loss = future_values - current_values

        # Transactions to make
        transactions_to_make = pd.DataFrame(self.portfolio.df_transaction_format)

        # First sell coins to free up funds
        # SELL: anything that's negative and over threshold and that we own
        id_coin_types_to_sell = coin_ids[(-1 * future_profit_loss >= self.threshold_sell) and (current_values > 0)]
        coin_types_to_sell = self.list_of_coin_types[id_coin_types_to_sell]
        # SELL Transaction: turn all coin_type into haven
        for idx, coin_type in enumerate(coin_types_to_sell):
            transaction_to_make = pd.DataFrame(
                {'type_coin_sold': coin_type, 'num_coin_sold': self.portfolio.num_coin_holding(coin_type),
                 'type_coin_bought': self.haven_coin.name})
            # concat will set nan all unpopulated df values .e.f ID / time copmleted
            transactions_to_make = pd.concat(transactions_to_make, transaction_to_make, ignore_index=True)

        # Orders for SELL
        self.manage_orders(df_transactions_to_make=transactions_to_make, timeout=60)

        # wipe transactions
        transactions_to_make = pd.DataFrame(self.portfolio.df_transaction_format)

        # Available funds? How many haven for trade?
        total_liquid_funds = self.portfolio.value_coin_holding(self.haven_coin.name)
        num_haven_for_buy_value = self.buy_value / self.haven_coin.price(self.haven_coin)

        # Now place buy orders
        # BUY transaction: anything positive that's over threshold and that we can afford
        id_coin_types_to_buy = coin_ids[future_profit_loss >= self.threshold_buy]
        coin_types_to_buy = self.list_of_coin_types[id_coin_types_to_buy]
        # BUY: buy coin_type with trade value's worth of haven
        for idx, coin_type in enumerate(coin_types_to_buy):
            if total_liquid_funds >= self.buy_value:
                transaction_to_make = pd.DataFrame(
                    {'type_coin_sold': self.haven_coin.name, 'num_coin_sold': num_haven_for_buy_value,
                     'type_coin_bought': coin_type})
                # concat will set nan all unpopulated df values .e.f ID / time copmleted
                transactions_to_make = pd.concat(transactions_to_make, transaction_to_make, ignore_index=True)
                total_liquid_funds -= self.buy_value  # can we still afford transactions?
            else:
                break

        # Orders for BUY
        self.manage_orders(df_transactions_to_make=transactions_to_make, timeout=60)

        # DONE

    def stop_trading(self):
        # stop trading so we can withdraw loads of money
        pass

    def liquidate_portfolio(self):
        # turn all coins into money - called manually
        pass

    def liquidate_coin(self, coin_type):
        # turn coin into money - called manually
        pass

    def manage_orders(self, df_transactions_to_make, timeout):
        # place orders, monitor and cancel after timeout
        # also cancel if price forecast changes?
        self.exchange.place_order(df_transactions_to_make)
        # loop
        self.exchange.query_order(df_transactions_to_make)
        # cancel orders which have been on the exchange too long / are no longer profitable
        self.exchange.cancel_order(df_transactions_to_make)
        # add to portfolio
        self.portfolio.record_transaction(df_transactions_to_make)
