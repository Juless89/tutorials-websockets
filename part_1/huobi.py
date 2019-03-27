import websocket
import gzip
from json import dumps, loads


# convert message to dict, decode, extract top ask/bid
def on_message(ws, message):
    data = loads(gzip.decompress(message).decode('utf-8'))
    
    if 'tick' in data:
        bid = data['tick']['bids'][0]
        ask = data['tick']['asks'][0]

        print(f'Top bid: {bid} top ask: {ask}')

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

# convert dict to string, subscribe to data streem by sending message
def on_open(ws):
    print(f'Connected to Huobi\n')
    params = {"sub": "market.steembtc.depth.step0", "id": "id1"}
    ws.send(dumps(params))

if __name__ == "__main__":
    # create websocket connection
    ws = websocket.WebSocketApp(
        url="wss://api.huobipro.com/ws",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )

    # keep connection alive
    ws.run_forever()

