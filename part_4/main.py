from binance import Binance
from huobi import Huobi
from upbit import Upbit
from datetime import datetime
from itertools import combinations 

import threading
import time


# calculate absolute delta in percentage
def delta(v1, v2):
    return abs((v2-v1)/v1)*100


# retrieve top bid/ask for each exchange
# calculate deltas
def calculate_price_delta(orderbooks, ex1, ex2):
    bid1 = float(orderbooks[ex1]['bids'][0][0])
    bid2 = float(orderbooks[ex2]['bids'][0][0])

    ask1 = float(orderbooks[ex1]['asks'][0][0])
    ask2 = float(orderbooks[ex2]['asks'][0][0])

    bid_ask = delta(bid1, ask2)
    ask_bid = delta(ask1, bid2)

    print(ex1, ex2, f'BID/ASK: {bid_ask:.2f}% ASK/BID: {ask_bid:.2f}%')

# return subsets of size 2 of all exchanges
def exchange_sets(orderbooks):
    exchanges = []

    # extract exchanges
    for exchange in orderbooks:
        if exchange != 'last_update':
            exchanges.append(exchange)

    return list(combinations(exchanges, 2))

# print top bid/ask for each exchange
# run forever
def run(orderbooks, lock):
    # local last_update
    current_time = datetime.now()

    sets = exchange_sets(orderbooks)

    while True:
        try:
            # check for new update
            if orderbooks['last_update'] != current_time:
                with lock:
                    # extract and print data
                    for exchanges in sets:
                        ex1, ex2 = exchanges
                        calculate_price_delta(orderbooks, ex1, ex2)
                    print(f"Last update: {orderbooks['last_update']}\n")

                    # set local last_update to last_update
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
        "Upbit": {},
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

    upbit = Upbit(
        url="wss://api.hitbtc.com/api/2/ws",
        exchange="Upbit",
        orderbook=orderbooks,
        lock=lock,
    )


    # start threads
    binance.start()
    huobi.start()
    upbit.start()

    # process websocket data
    run(orderbooks, lock)