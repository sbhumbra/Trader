import ccxt
import exchange
import fake_binance
import portfolio as P


class FakeExchange(exchange.Exchange):
    def __init__(self, timestamp, marketplace=ccxt.binance(), haven_marketplace=ccxt.bitfinex(),
                 haven_coin_type='USDT'):
        super(FakeExchange, self).__init__(marketplace, haven_marketplace, haven_coin_type)

        # Create a portfolio object; we can use this to populate fake_binance :)
        portfolio = P.Portfolio(timestamp, self)
        # Set fake marketplace
        self.marketplace = fake_binance.FakeBinance()
        self.marketplace.load_markets(True)
        # We can populate fake_binance from the portfolio:-)
        print('Populating fake exchange from real exchange...')
        self.marketplace.populate_from_portfolio(portfolio)
