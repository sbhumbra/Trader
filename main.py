import time
import keyboard
import manager as M

filename_coinstats = ''
filename_portfolio = ''

Autotrader = M.Manager(filename_coinstats=filename_coinstats, filename_portfolio=filename_portfolio)
Autotrader.portfolio.deposit(121, 'NEO', 1)
Autotrader.portfolio.deposit(6.85, 'LTC', 0.05)
BRun = True
tAutotraderWait = 0.5  # minutes
while BRun:
    Autotrader.trade()
    print('making loads')
    for i in range(1, int((tAutotraderWait * 60))):
        time.sleep(1)
        # listen for stop key
        if keyboard.is_pressed('space'):
            print('buy lambo')
            BRun = False
            break
Autotrader.stop_trading()
