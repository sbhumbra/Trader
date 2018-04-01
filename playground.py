import time
import manager as M

available_coin_types = ['ETH']
num_iterations = 200
time_sleep = 0.1

iteration_interval = 3 * 60

time_begin_default = 1520708240 - 3600 * 24 * 2
# 1518305400 # use this for repeatable testing (flat market)

latest_time = int(time.time())
# need to make sure we don't go into the future...
time_begin = time_begin_default - (num_iterations * iteration_interval)

flag_fake_exchange = True

A = M.Manager(time_begin, flag_fake_exchange,available_coin_types)

for idx in range(0, num_iterations):
    now = time_begin + idx * iteration_interval

    flag_calculate_return = A.trade(now)
    print('')
    print('making loads')
    print('')
    if flag_calculate_return:
        A.calculate_return(now)

    time.sleep(time_sleep)
