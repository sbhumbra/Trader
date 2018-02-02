import time

import exchange as E
import manager as M


def db_get_dummy_buy_transaction():
    test = M.Manager()
    pass


def db_get_dummy_sell_transaction():
    test = M.Manager()
    return test.sell_coins(['BTC', 'ETH', 'BNB'], [10, 10, 10])


def db_place_dummy_order(test_transaction):
    test_exchange = E.Exchange(['BTC', 'ETH', 'BNB', 'BCC', 'LTC', 'NEO'])
    test_exchange.place_order(test_transaction)


def db_query_dummy_order(test_transaction):
    test_exchange = E.Exchange(['BTC', 'ETH', 'BNB', 'BCC', 'LTC', 'NEO'])
    test_exchange.query_order(test_transaction)


def db_cancel_dummy_order(test_transaction):
    test_exchange = E.Exchange(['BTC', 'ETH', 'BNB', 'BCC', 'LTC', 'NEO'])
    test_exchange.cancel_order(test_transaction)


def db_forecast():
    a = M.Manager()
    a.forecaster.forecast('NEO', int(time.time()) + 10 * 60)
