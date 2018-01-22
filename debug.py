import manager as M
import exchange as E
import coinstats as C
import time


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


def db_manage_orders():
    test_manager = M.Manager()
    test_manager.portfolio.deposit(1000,'USDT',1000)
    test_transaction = test_manager.buy_coins(['BTC', 'ETH', 'BNB'], [10, 10, 10], 100000)
    test_manager.manage_orders(test_transaction, 60)
    test_transaction = test_manager.sell_coins(['BTC', 'ETH', 'BNB'], [9, 9, 9])
    test_manager.manage_orders(test_transaction, 60)
    return test_manager.portfolio


def db_get_set_coinstats():
    now = int(time.time())
    coin_types = ['BTC', 'ETH', 'BNB']
    test_coinstats = C.CoinStats(coin_types)
    test_coinstats.set_last_valid_price('BTC', 10, now)
    test_coinstats.set_last_valid_supply('BTC', 100, now)
    test_coinstats.set_last_valid_price('ETH', 10, now + 10)
    test_coinstats.set_last_valid_supply('ETH', 100, now + 10)
    #   coinstats should be created with all possible coins
    #   i.e. we shouldn't ever try to access a coin that's not there
    #   TODO: Handle this gracefully? Add new coin?
    [price, timestamp] = test_coinstats.get_last_valid_price('BTC')
    print('BTC: (price: ' + str(price) + ' ; time: ' + str(timestamp) + ')')

    [supply, timestamp] = test_coinstats.get_last_valid_supply('ETH')
    print('ETH: (supply: ' + str(supply) + ' ; time: ' + str(timestamp) + ')')

    return test_coinstats
