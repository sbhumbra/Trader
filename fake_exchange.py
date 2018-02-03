import ccxt
import exchange
import fake_binance


class FakeExchange(exchange.Exchange):
    def __init__(self, marketplace=ccxt.binance(), haven_marketplace=ccxt.bitfinex(),
                 haven_coin_type='USDT'):
        super(FakeExchange, self).__init__(marketplace, haven_marketplace, haven_coin_type)

        # Set fake marketplace
        self.marketplace = fake_binance.FakeBinance()
        print('Populating fake exchange from real exchange...')
        self.marketplace.populate_coin_portfolio(marketplace,self.num_exchange_query_tolerance)
