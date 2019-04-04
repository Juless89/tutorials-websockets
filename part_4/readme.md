![banner.png](https://steemitimages.com/640x0/https://res.cloudinary.com/hpiynhbhq/image/upload/v1515886103/kmzfcpvtzuwhvqhgpyjp.png)

---

#### Repository
https://github.com/python

#### What will I learn

- Connecting to Upbit
- Change data format
- Create subsets of exchanges
- Comparing top bid/ask on each update


#### Requirements

- Python 3.7.2
- Pipenv
- websocket-client
- requests

#### Difficulty

- intermediate

---

### Tutorial

#### Preface

Websockets allow for real time updates while putting less stress on the servers than API calls would. They are especially useful when data is updated frequently, like trades and the orderbooks on crypto currency exchanges. This tutorial will look at how to connect to the Upbit exchange, bringing the total connected exchanges to three. In addition the top bid and ask of all exchanges will be compared to each other in pairs.

This tutorial is part of a series, if anything is unclear refer to the previous tutorials.
#### Setup

Download the files from Github and install the virtual environment

```
$ cd ~/
$ git clone https://github.com/Juless89/tutorials-websockets
$ cd tutorials-websockets
$ pipenv install
$ pipenv shell
$ cd part_4
```

#### Connecting to Upbit

Like any other websocket or API interface start of by reading the documentation of the service provider. In this case that would be the [Upbit API Documentation](https://api.hitbtc.com/#about-companyname-api). 

Upbit's websocket interface works by connecting to the websocket and then subscribing to the data stream. This is done by sending a message with the `method`, `params` and `id`. `method` refers to which the function, in this case `subscribeOrderbook`. While params contains the required parameters to do so. `id` gets returned as is. 

```
# main.py

upbit = Upbit(
    url="wss://api.hitbtc.com/api/2/ws",
    exchange="Upbit",
    orderbook=orderbooks,
    lock=lock,
)

# upbit.py

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

```

After subscribing to a specific market the first reply is the full orderbook snapshot. Any reply after contains updates to the orderbook. Similar to the diff. depth stream from Binance is part 2. Replies have the following data structure.

```
{
  "jsonrpc": "2.0",
  "method": "snapshotOrderbook",
  "params": {
    "ask": [
      {
        "price": "0.054588",
        "size": "0.245"
      },
      {
        "price": "0.054590",
        "size": "0.000"
      },
      {
        "price": "0.054591",
        "size": "2.784"
      }
    ],
    "bid": [
      {
        "price": "0.054558",
        "size": "0.500"
      },
      {
        "price": "0.054557",
        "size": "0.076"
      },
      {
        "price": "0.054524",
        "size": "7.725"
      }
    ],
    "symbol": "ETHBTC",
    "sequence": 8073827,    
    "timestamp": "2018-11-19T05:00:28.193Z"
  }
}
```

The method is either `snapshotOrderbook` or `updateOrderbook`. `sequence` is used to stay synchronised with the exchange. The next update should always be `sequence+1`. If not all data should be dropped and the the stream should be restarted.

```
# convert message to dict, process update
def on_message(self, message):
    data = loads(message)

    # first message is the full snapshot
    if data['method'] == 'snapshotOrderbook':
        # process data

        self.orderbook['sequence'] = params['sequence']
    # following messages are updates to the orderbook
    elif data['method'] == 'updateOrderbook':
        # track sequence to stay in sync
        if params['sequence'] == self.orderbook['sequence']+1:
            self.orderbook['sequence'] = params['sequence']
            self.process_updates(params)
        else:
            print('Out of sync, abort')
```


The new data structure of the applications is now:


![Screenshot 2019-04-04 15.19.06.png](https://cdn.steemitimages.com/DQmcc5NSyuk6SPVAQALxRyqRcrxVEQNgEfn7wjnWV7c8vGz/Screenshot%202019-04-04%2015.19.06.png)

Each exchange thread writes the exchange data to the shared `Orderbooks` dict. The main processing thread looks at the `last_update` variable to determine if there is any new data. If so, the `Orderbooks` gets locked and the data can be processed.


![websockets_part4.gif](https://cdn.steemitimages.com/DQmeC29t8obtqAihcNNLnKSkRmjLRV2H9FGoqTEvsWs3YSs/websockets_part4.gif)


#### Change data format

As shown above the orderbook values get returned as a list of dicts. With the keys: `price` and `size`. In order easily process data from all exchanges all data should have the same format. Until now the data structure for the orderbooks has been like:

```
{
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

Python allows for list comprehensions which makes converting the dicts into the preferred lists quite simple.

```
# upbit.py

# first message is the full snapshot
if data['method'] == 'snapshotOrderbook':
    # extract params
    params = data['params']

    # convert data to right format
    self.orderbook['bids'] = [[x['price'], x['size']] for x in params['bid']]
    self.orderbook['asks'] = [[x['price'], x['size']] for x in params['ask']]

    self.orderbook['sequence'] = params['sequence']
```

`[[x['price'], x['size']] for x in params['bid']]` is telling python to create a list of lists that look like `[[x['price'], x['size']]` for each value `x` inside `params['bid']`.

This code is equivalent to:

```
list = []

for x in params['bid']:
    list.append([x['price'], x['size']])
```

#### Create subsets of exchanges

To compare the top bid/ask from each exchange with each other in pairs of two all possible unordered subsets have to be determined. Depending on how many exchanges one is connected to the amount of subsets increases drastically. This is known as `binomial coefficient`.


![Screenshot 2019-04-04 14.52.10.png](https://cdn.steemitimages.com/DQmXKqh99hhNYKPaYy3BMbM4Yh2RRwU3VABWcovS6G9CDy6/Screenshot%202019-04-04%2014.52.10.png)

Luckily python contains the libraby for just that. `n` refers to the amount of elements or exchanges in this case. and `k` is the size of the subset, or 2 in this case. First all exchanges are extracted from the shared orderbooks dicts. Then `combinations` is used to create all subsets.

```
# return subsets of size 2 of all exchanges
def exchange_sets(orderbooks):
    exchanges = []

    # extract exchanges
    for exchange in orderbooks:
        if exchange != 'last_update':
            exchanges.append(exchange)

    # return all subsets
    return list(combinations(exchanges, 2))
```

Result:

```
[('Binance', 'Huobi'), ('Binance', 'Upbit'), ('Huobi', 'Upbit')]

# adding 1 exchange results in quite a lot more subsets
[('Binance', 'Huobi'), ('Binance', 'Upbit'), ('Binance', 'Exchange'), ('Huobi', 'Upbit'), ('Huobi', 'Exchange'), ('Upbit', 'Exchange')]
```


Each exchange can be seen as a `node` that is connected to all other nodes. Each arrow represents a subset.


![Screenshot 2019-04-04 15.23.19.png](https://cdn.steemitimages.com/DQmSpyJLkMmWGz4nZZSmwTzHDPzYdvVqYZNpLBPGqkW6G6t/Screenshot%202019-04-04%2015.23.19.png)

#### Comparing top bid/ask on each update

To compare all exchange pairs on each update the exchange names, which are equivalent to the `key` values for the shared `orderbooks` dict, are extracted and then passed on to `calculate_price_delta()`

```
# main.py

if orderbooks['last_update'] != current_time:
    with lock:
        # extract and print data
        for exchanges in sets:
            ex1, ex2 = exchanges
            calculate_price_delta(orderbooks, ex1, ex2)
        print(f"Last update: {orderbooks['last_update']}\n")

        # set local last_update to last_update
        current_time = orderbooks['last_update']
```

The top bid/ask values are extracted from the `orderbooks` dict and converted to floats. Then the absolute difference is calculated by `delta()` and converted into a percentage. This is done for each pair of Exchanges.

```
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

    bid = delta(bid1, bid2)
    ask = delta(ask1, ask2)

    print(f'{ex1}-{ex2}\tBID Δ: {bid:.2f}% ASK Δ: {ask:.2f}%')
```

The result is a delta in % from the bid of both exchanges and the ask of both exchanges. The percentage is calculated relative to the first of the two exchanges.


![websockets_part4_2.gif](https://cdn.steemitimages.com/DQmNof3ajrZTwD4ZrdYbdEgzy9sU73ZhbTRBiwsqQsJ42Uw/websockets_part4_2.gif)



### Curriculum
- [Part 1: Connecting to STEEM orderbook stream via websockets on different exchanges](https://steemit.com/utopian-io/@steempytutorials/part-1-connecting-to-steem-orderbook-stream-via-websockets-on-different-exchanges)
- [Part 2: Manage local 'STEEM' orderbook via websocket stream from exchange](https://steemit.com/utopian-io/@steempytutorials/part-2-manage-local-steem-orderbook-via-websocket-stream-from-exchange)
- [Part 3: Connecting and managing multiple websocket streams in parallel](https://steemit.com/utopian-io/@steempytutorials/part-3-connecting-and-managing-multiple-websocket-streams-in-parallel)


---

The code for this tutorial can be found on [Github](https://github.com/Juless89/tutorials-websockets)!

This tutorial was written by @juliank.