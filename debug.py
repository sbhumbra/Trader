import manager as M
import exchange as E


def db_get_dummy_transactions():
    test = M.Manager()
    return test.buy_coins(['BTC', 'ETH', 'BNB'], [10, 10, 10], 100000)


def db_make_dummy_transactions():
    test_transaction = db_get_dummy_transactions()
    test_exchange = E.Exchange(['BTC', 'ETH', 'BNB', 'BCC', 'LTC', 'NEO'],flag_fake_exchange=True)
    test_exchange.place_order(test_transaction)
    return test_transaction
