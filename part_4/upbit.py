from client import Client
from json import loads, dumps
from datetime import datetime


class Upbit(Client):
    def __init__(self, url, exchange, orderbook, lock):
        super().__init__(url, exchange)

        # local data management
        self.orderbook = orderbook[exchange]
        self.lock = lock
        self.updates = 0
        self.last_update = orderbook

    # convert message to dict, process update
    def on_message(self, message):
        data = loads(message)

        # first message is the full snapshot
        if data['method'] == 'snapshotOrderbook':
            # extract params
            params = data['params']

            # convert data to right format
            self.orderbook['bids'] = [[x['price'], x['size']] for x in params['bid']]
            self.orderbook['asks'] = [[x['price'], x['size']] for x in params['ask']]

            self.orderbook['sequence'] = params['sequence']
        # following messages are updates to the orderbook
        elif data['method'] == 'updateOrderbook':
            # extract params
            params = data['params']

            # track sequence to stay in sync
            if params['sequence'] == self.orderbook['sequence']+1:
                self.orderbook['sequence'] = params['sequence']
                self.process_updates(params)
            else:
                print('Out of sync, abort')

    # Loop through all bid and ask updates, call manage_orderbook accordingly
    def process_updates(self, data):
        with self.lock:
            for update in [[x['price'], x['size']] for x in data['bid']]:
                self.manage_orderbook('bids', update)
            for update in [[x['price'], x['size']] for x in data['ask']]:
                self.manage_orderbook('asks', update)
            self.last_update['last_update'] = datetime.now()

    # Update orderbook, differentiate between remove, update and new
    def manage_orderbook(self, side, update):
        # extract values
        price, qty = update

        # loop through orderbook side
        for x in range(0, len(self.orderbook[side])):
            if price == self.orderbook[side][x][0]:
                # when qty is 0 remove from orderbook, else
                # update values
                if qty == 0:
                    del self.orderbook[side]
                    break
                else:
                    self.orderbook[side][x] = update
                    break
            # if the price level is not in the orderbook, 
            # insert price level, filter for qty 0
            elif ((price > self.orderbook[side][x][0] and side == 'bids') or
                    (price < self.orderbook[side][x][0] and side == 'asks')):
                if qty != 0:
                    self.orderbook[side].insert(x, update)
                    break
                else:
                    break

    # register to orderbook stream
    def on_open(self):
        super().on_open()
        params = {
            "method": "subscribeOrderbook",
            "params": {
                "symbol": "STEEMBTC"
            },
            "id": 1
        }
        self.ws.send(dumps(params))
