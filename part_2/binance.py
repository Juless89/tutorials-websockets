import websocket
import requests
from json import loads

class Client():
    def __init__(self):
        # create websocket connection
        self.ws = websocket.WebSocketApp(
            url="wss://stream.binance.com:9443/ws/steembtc@depth",
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )

        # local data management
        self.orderbook = {}
        self.updates = 0

    # keep connection alive
    def run_forever(self):
        self.ws.run_forever()

    # convert message to dict, process update
    def on_message(self, message):
        data = loads(message)

        # check for orderbook, if empty retrieve
        if len(self.orderbook) == 0:
            self.orderbook = self.get_snapshot()

        # get lastUpdateId
        lastUpdateId = self.orderbook['lastUpdateId']

        # drop any updates older than the snapshot
        if self.updates == 0:
            if data['U'] <= lastUpdateId+1 and data['u'] >= lastUpdateId+1:
                print(f'lastUpdateId {data["u"]}')
                self.orderbook['lastUpdateId'] = data['u']
                self.process_updates(data)
            else:
                print('discard update')
            
        # check if update still in sync with orderbook
        elif data['U'] == lastUpdateId+1:
            print(f'lastUpdateId {data["u"]}')
            self.orderbook['lastUpdateId'] = data['u']
            self.process_updates(data)
        else:
            print('Out of sync, abort')

    # catch errors
    def on_error(self, error):
        print(error)

    # run when websocket is closed
    def on_close(self):
        print("### closed ###")

    # run when websocket is initialised
    def on_open(self):
        print('Connected to Binance\n')

    # Loop through all bid and ask updates, call manage_orderbook accordingly
    def process_updates(self, data):
        for update in data['b']:
            self.manage_orderbook('bids', update)
        for update in data['a']:
            self.manage_orderbook('asks', update)
        print()

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
                    print(f'Removed {price} {qty}')
                    break
                else:
                    self.orderbook[side][x] = update
                    print(f'Updated: {price} {qty}')
                    break
            # if the price level is not in the orderbook, 
            # insert price level, filter for qty 0
            elif price > self.orderbook[side][x][0]:
                if qty != 0:
                    self.orderbook[side].insert(x, update)
                    print(f'New price: {price} {qty}')
                    break
                else:
                    break

    # retrieve orderbook snapshot
    def get_snapshot(self):
        r = requests.get('https://www.binance.com/api/v1/depth?symbol=STEEMBTC&limit=1000')
        return loads(r.content.decode())

if __name__ == "__main__":
    # create webscocket client
    client = Client()

    # run forever
    client.run_forever()
    


