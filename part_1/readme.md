![banner.png](https://steemitimages.com/640x0/https://res.cloudinary.com/hpiynhbhq/image/upload/v1515886103/kmzfcpvtzuwhvqhgpyjp.png)

---

#### Repository
https://github.com/python

#### What will I learn

- Basics of websockets
- Subscribing to data feeds
- Processing messages
- Return top bid/ask


#### Requirements

- Python 3.7.2
- Pipenv
- websocket-client

#### Difficulty

- basic

---

### Tutorial

#### Preface

Websockets allow for real time updates while putting less stress on the servers than API calls would. They are especially useful when data is updated frequently, like trades and the orderbooks on crypto currency exchanges. 

#### Setup

Download the files from Github and install the virtual environment

```
$ cd ~/
$ git clone https://github.com/Juless89/tutorials-websockets
$ cd tutorials-websockets
$ pipenv install
$ pipenv shell
$ cd part_1
```

#### Basics of websockets
Depending on which websocket one wants to connect to and how the serverside socket has been implemented there are multiple variations. However, in general when connecting to a websocket the following functions are essential. These are `on_message`, `on_error`, `on_close` and `on_open`.
When connecting to a websocket it is recommended to read the documentation of the service that is providing the websocket. An object `WebSocketApp` is created, the functions are passed to overwrite the generic functions and the `url` is the endpoint of the service. 

```
import websocket

def on_message(ws, message):
    print(message)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    print('Connected to websocket')

if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        url="wss://stream.binance.com:9443/ws/steembtc@depth20",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )

    ws.run_forever()
```

`on_open` gets called immediatly after creating the connection, before receiving any messages. When additinal parameters are required this is where they get set. `on_message` deals with all messages received through the websocket, extracting and processing data should be implemented here. `on_error` gets called when an error occurs, error handling should be implemented here. `on_close` get called when the connection gets closed, either by the client or the server. `run_forever` makes sure the connection stays alive. 



#### Subscribing to data feeds

This tutorial will look at connecting to two different exchanges via websockets and get a live data feed of the STEEM orderbook. The exchanges are Binance and Huobi and both use a different technique to subscribe to different data feeds. Always read the documentation provided by the websocket service provider.

![Screenshot 2019-03-27 13.02.40.png](https://cdn.steemitimages.com/DQmTaLE7aJWvRcAFuydAA7fYidVkA7vFAqtWGhTwyVg3Fwz/Screenshot%202019-03-27%2013.02.40.png)

[Binance documentation](https://github.com/binance-exchange/binance-official-api-docs/blob/master/web-socket-streams.md)

Binance uses the url to differantiate between data feeds. For this tutorial a stream will be set up for the partial book depth. Taken directly from the documentation:

```
The base endpoint is: wss://stream.binance.com:9443

Raw streams are accessed at /ws/<streamName>

Top <levels> bids and asks, pushed every second. Valid <levels> are 5, 10, or 20.

Stream Name: <symbol>@depth<levels>

```

Connecting to the steembtc partial book depth for 20 levels is then achieved by connecting to the url: `wss://stream.binance.com:9443/ws/steembtc@depth20`.

![binance.gif](https://cdn.steemitimages.com/DQmc9zkPw99vE6ML3HzbMprTCzpMRMh13M6mkoqU15XQWfC/binance.gif)

---

![Screenshot 2019-03-27 13.03.01.png](https://cdn.steemitimages.com/DQmbFKJdLrzNKAvaoZbhWaaaA6Sr1xt3PxeRVkXKwMyyTDa/Screenshot%202019-03-27%2013.03.01.png)

[Huobi documentation](https://github.com/huobiapi/API_Docs_en/wiki/Huobi-API)

Huobi uses a subscribe based system. Where the client must subscribe to data streams after the connection has been made. Taken from their documentation:

```
SSL Websocket Connection
wss://api.huobi.pro/ws

Subscribe
To receive data you have to send a "sub" message first.

Market Depth	market.$symbol.depth.$type	$type ：{ step0, step1, step2, step3, step4, step5 } （depths 0-5）

//request
{
  "sub": "topic to sub",
  "id": "id generate by client"
}
```

Subscribing to the level 0 market depth of steembtc is achieved by connection to `wss://api.huobi.pro/ws` and then sending the message which contains `"sub": "market.eosusdt.depth.step0"`. Sending the message is done by using `send()`. The dict has to be converted to a string first, which is done by using `dumps()`

```
from json import dumps

def on_open(ws):
    print('Connected to websocket')
    params = {"sub": "market.steembtc.depth.step0", "id": "id1"}
    ws.send(dumps(params))
```

Will return the following reply on success:
```
{'id': 'id1', 'status': 'ok', 'subbed': 'market.steembtc.depth.step0', 'ts': 1553688645071}

![huobi.gif](https://cdn.steemitimages.com/DQmdC1aBRzoxsiX4oJq5m1dKo3kf5NskaNWhyuG7axbqpuq/huobi.gif)
```


#### Processing messages

Every service is different and in most cases return data in a different format, noting again the importance of the documentation.

Binance
```
Payload:

{
  "lastUpdateId": 160,  // Last update ID
  "bids": [             // Bids to be updated
    [
      "0.0024",         // Price level to be updated
      "10"              // Quantity
    ]
  ],
  "asks": [             // Asks to be updated
    [
      "0.0026",         // Price level to be updated
      "100"            // Quantity
    ]
  ]
}
```

All data gets returned as a string and has to be converted to a dict to access. This is done by using `loads()` from the JSON library.

```
def on_message(self, message):
    print(loads(message))
    print()
```

Huobi return the data encoded and requires one additional step.

```
import gzip

def on_message(self, message):
    print(loads(gzip.decompress(message).decode('utf-8')))
    print()
```

Data format:
```
{
	'ch': 'market.steembtc.depth.step0',
	'ts': 1553688645047,
	'tick': {
		'bids': [
			[0.00010959, 736.0],
			[0.00010951, 372.0],
			[0.0001095, 56.0],
			[0.00010915, 1750.0],
			[0.00010903, 371.77],
			[0.00010891, 1684.65],
		],
		'asks': [
			[0.00011009, 368.0],
			[0.00011025, 1575.36],
			[0.00011039, 919.0],
			[0.00011054, 92.0],
			[0.00011055, 68.85],
			[0.00011077, 736.77],
		],
		'ts': 1553688645004,
		'version': 100058128375
	}
}
```

In addition Huobi also sends pings to make sure the client is still online.
```
{'ping': 1553688793701}
```

When processing messages from Huobi this has to be filtered out.

#### Return top bid/ask

For Binance returning the top bid/ask is straight forward as the messages always have the same format.

```
def on_message(self, message):
    data = loads(message)
    bid = data['bids'][0]
    ask = data['asks'][0]

    print(f'Top bid: {bid} top ask: {ask}')
```

Due to the ping messages doing the same for Huobi requires one additional step.
```
def on_message(self, message):
    data = loads(gzip.decompress(message).decode('utf-8'))
    
    if 'tick' in data:
        bid = data['tick']['bids'][0]
        ask = data['tick']['asks'][0]

        print(f'Top bid: {bid} top ask: {ask}')
```

#### Running the code


`python binance.py`
![binance2.gif](https://cdn.steemitimages.com/DQmZjdYqJoarQHSqLGwGU3WJssp1HWV7ps9z2D5ryTUC9QN/binance2.gif)

`python huobi.py`
![huobi2.gif](https://cdn.steemitimages.com/DQmRDPoQxN9jCPfDT4jrK5qceHs3FXk3Sut5PDBXCMiS2C5/huobi2.gif)
---

The code for this tutorial can be found on [Github](https://github.com/Juless89/tutorials-websockets)!

This tutorial was written by @juliank.