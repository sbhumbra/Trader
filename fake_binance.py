import ccxt
import numpy as np
import copy


class FakeBinance(ccxt.binance):
    def __init__(self):
        super(FakeBinance, self).__init__()

        #   Track number of coins held
        self.fake_balance = {}
        self.fake_balance['free'] = {}

        self.cache = {}
        self.cache_width = 60

        d = self.describe()
        self.buy_fee = d['fees']['trading']['taker']
        self.sell_fee = d['fees']['trading']['maker']

        self.num_transactions = 0

    def populate_from_portfolio(self, portfolio):
        current_holdings = copy.deepcopy(portfolio.current_holdings)
        self.fake_balance = {}
        self.fake_balance['free'] = {}
        while current_holdings:
            # Remove coin from the list (while loop ends at empty list)
            coin_held = current_holdings.popitem()
            print(coin_held)
            self.fake_balance['free'][coin_held[0]] = coin_held[1]['num']
            self.fake_balance[coin_held[0]] = {'free': coin_held[1]['num']}

    def fetch_ohlcv(self, symbol, timeframe='1m', since=None, limit=None, params={}):
        key = symbol + timeframe  # blame Luca
        try:
            cached_candles = self.cache[key]

            if cached_candles[0][0] > since:
                raise Exception

            cached_section = [candle for candle in cached_candles if candle[0] >= since]

            if len(cached_section) < self.cache_width:
                raise Exception

            return [candle for candle in cached_candles if candle[0] >= since]
        except:
            self.cache[key] = super(FakeBinance, self).fetch_ohlcv(symbol, timeframe, since)
            return self.cache[key]

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
        if trade_amount < 0:
            print('Trade amount: ' + str(trade_amount))
            raise Exception('Fake exchange: invalid trade quantity!!')

        flag_waiting_for_bids = True
        while flag_waiting_for_bids:
            order_book = self.fetch_order_book(symbol)
            bids = np.asarray(order_book[market_price]) if len(order_book[market_price]) > 0 else None
            if bids.any():
                bid_average = np.median(bids, axis=0)
                bid_average = bid_average[0]  # first element is exchange rate, second element is amount

                if market_price == 'asks':
                    # Buying: increase a coin by trade amount and decrease another using bid average and fee
                    self.decrease_coin_holding(coin_type_sold, trade_amount * bid_average * (1 - trade_fee))
                    self.increase_coin_holding(coin_type_bought, trade_amount)
                else:
                    # Selling: decrease a coin by trade amount and increase another using bid average and fee
                    self.decrease_coin_holding(coin_type_sold, trade_amount)
                    self.increase_coin_holding(coin_type_bought, trade_amount * bid_average * (1 - trade_fee))

                self.num_transactions += 1
                flag_waiting_for_bids = False

    def fetch_order(self, id, symbol=None, params=None):
        return {'status': 'closed'}

    def cancel_order(self, id, symbol=None, params=None):
        pass

    def fetch_balance(self, params=None):
        return self.fake_balance

    def increase_coin_holding(self, coin_type, amount):
        self.fake_balance[coin_type]['free'] += amount

    def decrease_coin_holding(self, coin_type, amount):
        if self.fake_balance[coin_type]['free'] < amount:
            raise ccxt.errors.InsufficientFunds

        self.fake_balance[coin_type]['free'] -= amount
