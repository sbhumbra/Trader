import time
import keyboard
import manager as M
import numpy as np

tAutotraderWait = 15  # seconds
flag_fake_exchange = True

Autotrader = M.Manager(flag_fake_exchange)

BRun = True
while BRun:
    Autotrader.trade()
    print('making loads')
    print('')
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
Autotrader.stop_trading()
