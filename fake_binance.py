import ccxt
import numpy as np


class FakeBinance(ccxt.binance):
    def __init__(self):
        super(FakeBinance, self).__init__()

        #   Track number of coins held
        self.coin_holdings = self.create_blank_coin_portflio()
        d = self.describe()
        self.buy_fee = d['fees']['trading']['taker']
        self.sell_fee = d['fees']['trading']['maker']

        self.num_transactions = 0

    def populate_coin_portfolio(self, marketplace, num_exchange_query_tolerance):
        num_attempts = 0
        while num_attempts < num_exchange_query_tolerance:
            try:
                balance = marketplace.fetch_balance()
                balance = balance['free']
                coins_held = [[coin_type, balance[coin_type]] for coin_type in balance if balance[coin_type] > 0]
                for idx in range(1, len(coins_held)):
                    coin_held = coins_held[idx]
                    coin_type_held = coin_held[0]
                    num_coin_held = coin_held[1]
                    self.coin_holdings[coin_type_held]['free'] = num_coin_held

                trim = self.coin_holdings.pop('ALEXCOIN')
                trim = self.coin_holdings.pop('LUCACOIN')
                return
            except:
                num_attempts += 1

        raise Exception("ERROR: FakeBinance num_coin_holding - unable to get value from exchange")

    def create_blank_coin_portflio(self):
        # This is a Python structure.
        # The behaviour is similar to a Matlab structure i.e. we can add fields as required
        return {'ALEXCOIN': {'free': 0},
                'LUCACOIN': {'free': 0},
                }

    def create_market_buy_order(self, symbol, amount, params=None):
        coin_type_bought = symbol.split('/')[0]  # left side, e.g. 'NEO','BNB',...
        coin_type_sold = symbol.split('/')[1]  # right side, e.g. 'USDT',...

        self.create_fake_order(symbol, coin_type_bought, coin_type_sold, amount, self.buy_fee, 'asks')

        return {'id': self.num_transactions}

    def create_market_sell_order(self, symbol, amount, params=None):
        coin_type_bought = symbol.split('/')[1]  # right side, e.g. 'USDT',...
        coin_type_sold = symbol.split('/')[0]  # left side, e.g. 'NEO','BNB',...

        self.create_fake_order(symbol, coin_type_bought, coin_type_sold, amount, self.sell_fee, 'bids')

        return {'id': self.num_transactions}

    def create_fake_order(self, symbol, coin_type_bought, coin_type_sold, trade_amount, trade_fee, market_price):
        flag_waiting_for_bids = True
        while flag_waiting_for_bids:
            order_book = self.fetch_order_book(symbol)
            bids = np.asarray(order_book[market_price]) if len(order_book[market_price]) > 0 else None
            if bids.any():
                bid_average = np.median(bids, axis=0)
                bid_average = bid_average[0]  # first element is exchange rate, second element is amount

                self.decrease_coin_holding(coin_type_sold, trade_amount)
                self.increase_coin_holding(coin_type_bought, trade_amount * bid_average * (1 - trade_fee))
                self.num_transactions += 1
                flag_waiting_for_bids = False

    def fetch_order(self, id, symbol=None, params=None):
        return {'status': 'closed'}

    def cancel_order(self, id, symbol=None, params=None):
        pass

    def fetch_balance(self, params=None):
        return self.coin_holdings

    def increase_coin_holding(self, coin_type, amount):
        self.coin_holdings[coin_type]['free'] += amount

    def decrease_coin_holding(self, coin_type, amount):
        self.coin_holdings[coin_type]['free'] -= amount
