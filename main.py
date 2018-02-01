import time
import keyboard
import manager as M

Autotrader = M.Manager()
BRun = True
tAutotraderWait = 20  # minutes
while BRun:
    Autotrader.trade()
    print('making loads')
    print('')
    for i in range(1, int((tAutotraderWait * 60))):
        time.sleep(1)
        # listen for stop key
        if keyboard.is_pressed('space'):
            print('buy lambo')
            BRun = False
            break
Autotrader.stop_trading()
