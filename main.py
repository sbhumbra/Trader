import manager as M
import keyboard

Autotrader = M.Manager()
BRun = True
while BRun:
    Autotrader.trade()
    print('making loads')
    # listen for stop key
    if keyboard.is_pressed('space'):
        print('buy lambo')
        BRun = False
