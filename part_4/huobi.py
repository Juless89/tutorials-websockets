from client import Client
from json import loads, dumps
from datetime import datetime

import gzip


# inherits from Client
class Huobi(Client):
    # call init from parent class
    def __init__(self, url, exchange, orderbook, lock):
        super().__init__(url, exchange)

        # local data management
        self.orderbook = orderbook[exchange]
        self.lock = lock
        self.last_update = orderbook

    # convert message to dict, decode, extract top ask/bid
    def on_message(self, message):
        data = loads(gzip.decompress(message).decode('utf-8'))
        
        # extract bids/aks
        if 'tick' in data:
            with self.lock:
                self.orderbook['bids'] = data['tick']['bids']
                self.orderbook['asks'] = data['tick']['asks']
                self.last_update['last_update'] = datetime.now()

        # respond to ping message
        elif 'ping' in data:
            params = {"pong": "data['ping']"}
            self.ws.send(dumps(params))

    # convert dict to string, subscribe to data streem by sending message
    def on_open(self):
        super().on_open()
        params = {"sub": "market.steembtc.depth.step0", "id": "id1"}
        self.ws.send(dumps(params))