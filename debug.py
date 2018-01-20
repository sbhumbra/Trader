import manager as M
import exchange as E


def db_get_dummy_buy_transaction():
    test = M.Manager()
    return test.buy_coins(['BTC', 'ETH', 'BNB'], [10, 10, 10], 100000)


def db_get_dummy_sell_transaction():
    test = M.Manager()
    return test.sell_coins(['BTC', 'ETH', 'BNB'], [10, 10, 10])


def db_place_dummy_order(test_transaction):
    test_exchange = E.Exchange(['BTC', 'ETH', 'BNB', 'BCC', 'LTC', 'NEO'], flag_fake_exchange=True)
    test_exchange.place_order(test_transaction)


def db_query_dummy_order(test_transaction):
    test_exchange = E.Exchange(['BTC', 'ETH', 'BNB', 'BCC', 'LTC', 'NEO'], flag_fake_exchange=True)
    test_exchange.query_order(test_transaction)


def db_cancel_dummy_order(test_transaction):
    test_exchange = E.Exchange(['BTC', 'ETH', 'BNB', 'BCC', 'LTC', 'NEO'], flag_fake_exchange=True)
    test_exchange.cancel_order(test_transaction)
