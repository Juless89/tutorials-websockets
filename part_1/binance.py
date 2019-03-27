import websocket
from json import loads

# convert message to dict, extract top ask/bid
def on_message(ws, message):
    data = loads(message)
    bid = data['bids'][0]
    ask = data['asks'][0]

    print(f'Top bid: {bid} top ask: {ask}')

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    print('Connected to Binance\n')

if __name__ == "__main__":
    # create websocket connection
    ws = websocket.WebSocketApp(
        url="wss://stream.binance.com:9443/ws/steembtc@depth20",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )

    # keep connection alive
    ws.run_forever()


