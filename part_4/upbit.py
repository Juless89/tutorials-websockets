import websocket
from json import dumps, loads


# convert message to dict, decode, extract top ask/bid
def on_message(ws, message):
    data = loads(message)
    
    print(data)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

# convert dict to string, subscribe to data streem by sending message
def on_open(ws):
    print(f'Connected to Upbit\n')
    params = {
        "method": "subscribeOrderbook",
        "params": {
        "symbol": "ETHBTC"
        },
        "id": 123
    }
    ws.send(dumps(params))

if __name__ == "__main__":
    # create websocket connection
    ws = websocket.WebSocketApp(
        url="wss://api.hitbtc.com/api/2/ws",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )

    # keep connection alive
    ws.run_forever()

