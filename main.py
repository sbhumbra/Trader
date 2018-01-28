import time

import manager as M

filename_coinstats = ''
filename_portfolio = ''

Autotrader = M.Manager(filename_coinstats=filename_coinstats, filename_portfolio=filename_portfolio)
Autotrader.portfolio.deposit(70, 'NEO', 0.58941)
BRun = True
tAutotraderWait = 5  # minutes
while BRun:
    Autotrader.trade()
    print('making loads')
    for i in range(1, (tAutotraderWait * 60)):
        time.sleep(1)
        # listen for stop key
        if False:  # keyboard.is_pressed('space'):
            print('buy lambo')
            BRun = False
            break
Autotrader.stop_trading()
