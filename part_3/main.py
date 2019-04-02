from binance import Binance
from huobi import Huobi
from datetime import datetime

import threading
import time


# print top bid/ask for each exchange
# run forever
def run(orderbooks, lock):
    while True:
        current_time = datetime.now()
        try:
            if orderbooks['last_update'] != current_time:
                with lock:
                    # extract and print data
                    for key, value in orderbooks.items():
                        if key != 'last_update':
                            bid = value['bids'][0][0]
                            ask = value['asks'][0][0]
                            print(f"{key} bid: {bid} ask: {ask}")
                    print()
                    current_time = orderbooks['last_update']
            time.sleep(0.1)
        except Exception:
            pass


if __name__ == "__main__":
    # data management
    lock = threading.Lock()
    orderbooks = {
        "Binance": {},
        "Huobi": {},
        "last_update": None,
    }

    # create websocket threads
    binance = Binance(
        url="wss://stream.binance.com:9443/ws/steembtc@depth",
        exchange="Binance",
        orderbook=orderbooks,
        lock=lock,
    )

    huobi = Huobi(
        url="wss://api.huobipro.com/ws",
        exchange="Huobi",
        orderbook=orderbooks,
        lock=lock,
    )

    # start threads
    binance.start()
    huobi.start()

    # process websocket data
    run(orderbooks, lock)