import time
import keyboard
import manager as M
import numpy as np

tAutotraderWait = 180  # seconds
flag_fake_exchange = False

Autotrader = M.Manager(flag_fake_exchange)

BRun = True
while BRun:
    flag_calculate_return = Autotrader.trade()
    print('')
    print('making loads')
    print('')
    if flag_calculate_return:
        Autotrader.calculate_return()

    for idx in range(0, int(tAutotraderWait)):
        time_remaining = int(tAutotraderWait) - idx
        if not np.mod(time_remaining, 5):
            print(str(time_remaining) + ' seconds until next trade')

        time.sleep(1)
        # listen for stop key
        if keyboard.is_pressed('space'):
            print('buy lambo')
            BRun = False
            break
    print('')

# cash out
Autotrader.threshold_buy_ratio = 1000
Autotrader.threshold_sell_ratio = 500
Autotrader.trade()
Autotrader.stop_trading()
