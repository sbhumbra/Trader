import manager as M
import keyboard
import time

Autotrader = M.Manager()
BRun = True
tAutotraderWait = 5  # minutes
while BRun:
    Autotrader.trade()
    print('making loads')
    for i in range(1, (tAutotraderWait * 60)):
        time.sleep(1)
        # listen for stop key
        if keyboard.is_pressed('space'):
            print('buy lambo')
            BRun = False
            break
Autotrader.stop_trading()
