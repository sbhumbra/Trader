import scipy.io as sio
from binance.client import Client

api_things = sio.loadmat("api_things.mat")

client = Client(api_things["api_key"][0]
                , api_things["api_secret"][0]
                )

info = client.get_exchange_info()

print(info)
