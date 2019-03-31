![banner.png](https://steemitimages.com/640x0/https://res.cloudinary.com/hpiynhbhq/image/upload/v1515886103/kmzfcpvtzuwhvqhgpyjp.png)

---

#### Repository
https://github.com/python

#### What will I learn

- What is a local orderbook
- Open a diff. depth stream
- Retrieve orderbook snapshot
- Process updates
- Update the local orderbook


#### Requirements

- Python 3.7.2
- Pipenv
- websocket-client

#### Difficulty

- basic

---

### Tutorial

#### Preface

Websockets allow for real time updates while putting less stress on the servers than API calls would. They are especially useful when data is updated frequently, like trades and the orderbooks on crypto currency exchanges. This tutorial will look at managing a local orderbook. For this example the exchange Binance will be used. Depending on the service provider there can be slight modifications. This tutorial is a follow up for [part 1](https://steemit.com/utopian-io/@steempytutorials/part-1-connecting-to-steem-orderbook-stream-via-websockets-on-different-exchanges), if anything is unclear, go over the previous tutorial first.

#### Setup

Download the files from Github and install the virtual environment

```
$ cd ~/
$ git clone https://github.com/Juless89/tutorials-websockets
$ cd tutorials-websockets
$ pipenv install
$ pipenv shell
$ cd part_2
```

#### What is a local orderbook
In the previous tutorial a partial orderbook stream was created via a websocket. Meaning that only part of the orderbook was send on every update. This reduces the amount of data that has te be send every update. In the case a user wants to have the full orderbook updated via a websocket a different approach is needed. In general this works by first retrieving a full snapshot of the orderbook and then only receiving updates made to the orderbook. This greatly reduces the amount of data that has to be send on every update. However, this does mean the user has to update his version of the orderbook to stay synchronised. In addition, Every update comes with an `update id`, this allows the user to keep track of any missed updates and ensure the orderbook is synchronised.

Taken from the [Binance documentation](https://github.com/binance-exchange/binance-official-api-docs/blob/master/web-socket-streams.md) the instructions are as follows. This list will be referred to as the Binance to do list.

![Screenshot 2019-03-31 14.31.10.png](https://cdn.steemitimages.com/DQma9o83tuupwrSpsKfgug3sTWXqgvqtJy4QT2WtMBRChbW/Screenshot%202019-03-31%2014.31.10.png)

#### Open a diff. depth stream

The code from the previous update has been slightly adjusted. A class `Client` has been made to accommodate local data storage and keeping everything together. Also the websocket `url` has been set to `wss://stream.binance.com:9443/ws/steembtc@depth`. This completes step 1 of the Binance to do list. Step 2, the buffering, is done by the python websocket library automatically.

```
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

    # convert message to dict, print
    def on_message(self, message):
        data = loads(message)
        print(data)
        print()

    # catch errors
    def on_error(self, error):
        print(error)

    # run when websocket is closed
    def on_close(self):
        print("### closed ###")

    # run when websocket is initialised
    def on_open(self):
        print('Connected to Binance\n')

if __name__ == "__main__":
    # create webscocket client
    client = Client()

    # run forever
    client.run_forever()
```

![websockets_part2.gif](https://cdn.steemitimages.com/DQmRDfUEg9AFmxt51mRo6jpRYiZBpXgKvYYnhu8rhiE4nbB/websockets_part2.gif)

#### Retrieve orderbook snapshot

The depth snapshot can be retrieved by using a get request to `https://www.binance.com/api/v1/depth?symbol=STEEMBTC&limit=1000`. Data is returned in an encoded string. This has to be converted to a dict with `loads()` and decoded by `decode()`.


```
import requests

# retrieve orderbook snapshot
def get_snapshot(self):
    r = requests.get('https://www.binance.com/api/v1/depth?symbol=STEEMBTC&limit=1000')
    return loads(r.content.decode())
```

Data is returned in the following format. The `lastUpdateId` is important and will be used to synchronise the local orderbook with the updates from the websocket. This completes step 3.

```
{
  "lastUpdateId": 160,  // Last update ID
  "bids": [             // Bids
    [
      "0.0024",         // Price level 
      "10"              // Quantity
    ]
  ],
  "asks": [             // Asks
    [
      "0.0026",         // Price level
      "100"            // Quantity
    ]
  ]
}
```

#### Processing updates

Updates have the following data structure.

```
{
  "e": "depthUpdate", // Event type
  "E": 123456789,     // Event time
  "s": "BNBBTC",      // Symbol
  "U": 157,           // First update ID in event
  "u": 160,           // Final update ID in event
  "b": [              // Bids to be updated
    [
      "0.0024",       // Price level to be updated
      "10"            // Quantity
    ]
  ],
  "a": [              // Asks to be updated
    [
      "0.0026",       // Price level to be updated
      "100"           // Quantity
    ]
  ]
}
```

`U` and `u` are used to synchronise the orderbook. These are the `lastUpdateIds`. `b` and `a` contain the actual new values for the bids and asks. First there is a check done to see if there is already a snapshot in the local orderbook. Initially the `lastUpdateId` is set to 0 to differentiate between the situation where the snapshot has just been retrieved and may be out of sync. In which case older updates have to be dropped. Then after each update `u` is set as the `lastUpdateId`. For each new update `U` has to be equal to `lastUpdateId+1`. This completes step 4, 5 and 6 from the Binance to do list.


```
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
            print('process this update')
            self.orderbook['lastUpdateId'] = data['u']
        else:
            print('discard update')
        
    # check if update still in sync with orderbook
    elif data['U'] == lastUpdateId+1:
        print('process this update')
        self.orderbook['lastUpdateId'] = data['u']
    else:
        print('Out of sync, abort')
```

![websockets_part2_2.gif](https://cdn.steemitimages.com/DQmWt4fU9UbL3Vt6ERSuQTCUX1jJL8hRX9X4zgvgZXEN6aM/websockets_part2_2.gif)

#### Updating the local orderbook

The local orderbook is a dict containing the `lastUpdateId` and two lists `bids` and `asks`. The lists are ordered by the price level. There are three different possibilities for adjustments to the list.

- Price level already exists, different quantity
- New price level
- Price level quality set to 0, remove from list

Even though the values are strings, python is smart enough to understand when floats are implied. Two functions are used. `process_updates` is called from `on_message`: it loops through all the updates and differentiates between the bid and ask side. `manage_orderbook` then checks which type of adjustment should be made and executes this update into the orderbook.

```
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
```

#### Running the code


`python binance.py`

![websockets_part2_3.gif](https://cdn.steemitimages.com/DQmX5EVUTJaN45wgrimvQmZf3WsuQztujCiGnyokEZgMbmF/websockets_part2_3.gif)


---

The code for this tutorial can be found on [Github](https://github.com/Juless89/tutorials-websockets)!

This tutorial was written by @juliank.