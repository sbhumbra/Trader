import numpy as np
import ccxt


class Coin:
    def __init__(self, name, exchange=ccxt.binance()):
        self.name = name
        self.exchange = exchange
        self.last_valid_price = 0           # [$] - will initializing at zero cause trouble?
        self.last_valid_price_history = 0   # [$] - will initializing at zero cause trouble?
        self.last_valid_supply = 0          # [-]

    def price_history(self, haven_coin, period='1h',n_periods=6):
        # Returns [$]
        BIsHaven        = (self.name == haven_coin.name)
        BIsSinglePrice  = (period == '1m') and (n_periods == 1)

        # Get Haven Price History [$/Haven]
        if BIsHaven:
            # Price fetched from exchange will already be USD, therefore conversion factor is 1
            haven_to_usd = 1
        elif BIsSinglePrice:
            haven_to_usd = haven_coin.last_valid_price
        else:
            haven_to_usd = haven_coin.last_valid_price_history

        # Get Price History [Haven/Coin], for a given exchange
        if BIsHaven:
            coin_pair = haven_coin.name + '/USD'
        else:
            coin_pair = self.name + '/' + haven_coin.name

        try:
            # Get OHLCV in Haven per Coin
            # Last element is most recent (??)
            all_OHLCV = self.exchange.fetch_ohlcv(coin_pair, period)
            # Get V (closing value), still in Haven per Coin
            selected_OHLCV = np.asarray(all_OHLCV[-n_periods:], 'float')
            # Price [$] = Haven x Haven Price, elementwise
            price_history = np.multiply(selected_OHLCV[:, -2], haven_to_usd)
            # Store Price history if not single value
            if BIsSinglePrice:
                price_history = np.asscalar(price_history)
            else:
                self.last_valid_price_history = price_history
            return price_history
        except:
            if BIsSinglePrice:
                return self.last_valid_price
            else:
                return self.last_valid_price_history

    # Price is a special case of price history (period = 1m, n_periods = 1)
    # Last valid value logic addresses price or price history accordingly
    def price(self, haven_coin):
        # Returns [$]
        price = self.price_history(haven_coin, '1m', 1)
        self.last_valid_price = price
        return price

    def supply(self):
        # only coinmarketcap has the total supply
        try:
            ticker = ccxt.coinmarketcap().fetch_ticker(self.name+'/USD')
            supply = ticker['info']['available_supply']
            self.last_valid_supply = supply
        except:
            supply = self.last_valid_supply

        return supply

# using bitfinex for Haven pricing because it supports OHLCV format
Haven = Coin('ETH',ccxt.bitfinex())

# initialiase Haven price and price history
p = Haven.price(Haven)
#print(p)
#print(Haven.last_valid_price)
p = Haven.price_history(Haven)
#print(p)
#print(Haven.last_valid_price_history)

# Test with altcoin
# something strange with time history
blah = Coin('XVG')
print(blah.price(Haven))
print(Haven.last_valid_price)
print(blah.price_history(Haven))
print(Haven.last_valid_price_history)
print(blah.supply())
