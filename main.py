import time
import keyboard
import manager as M

filename_coinstats = ''
filename_portfolio = ''

Autotrader = M.Manager(filename_coinstats=filename_coinstats, filename_portfolio=filename_portfolio)
Autotrader.portfolio.deposit(1, 'BNB', 1.65526372)
Autotrader.portfolio.deposit(1, 'BTC', 0.00311611)
Autotrader.portfolio.deposit(1, 'NEO', 0.35477600)
Autotrader.portfolio.deposit(1, 'ETH', 0.02913826)
Autotrader.portfolio.deposit(123.85, 'USDT', 22.21477239)
BRun = True
tAutotraderWait = 30  # minutes
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
