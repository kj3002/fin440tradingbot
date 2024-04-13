from rit_api import *
import time
import matplotlib.pyplot as plt
import numpy as np


# TODO:
# Determine when to start program, or how to wait until game starts/repeat for multiple rounds
# Determine whether we can read who makes what positions, as using this information could be quite telling, especially for bluffs
# Determine optimal parameters: trade sizing, edge, fade, slack

# Game loop:
# Get start of game information (case, trader, limits)
# Set starter positions, e.g. traps for market orders that sweep the entire book
# Loop each tick:
#   Get current order book and portfolio
#   Determine fair price based on supply and demand (and our fair price based on our current position? fade factor in blog)
#   Determine target portfolio based on current portfolio
#   Set initial spread positions around fair price based on target portfolio
#       - This should be roughly even around fair price when our position is net zero
#         If we are long, we want to sell more aggressively, and vice versa
#         In LT1, (the first game) we get long and short positions of 5000 added to our current position,
#         so we will need to rebalance whenever this occurs. (fade should cover this)
#       - We want to "penny" out our competitors when rational. This means that we should 
#         develop a fudge factor (slack in blog) that we can tune that allows our spread to narrow or widen.
#   Set additional spreads at different increments within the order book to profit from partial order book sweeps (scales in blog)
#   Potentially place bluff orders into the order book, but at safe levels
#   Modify starter positions in the case we were 'penny'd out. 
#   Send and cancel orders
#


"""Note: need to change API Key depending on the machine"""
HOST = None
API_KEY = None
if len(sys.argv) < 3:
    HOST = "http://localhost:10001/v1"
    API_KEY = "STWSSJQT"
else:
    HOST = sys.argv[1]
    API_KEY = sys.argv[2]


init(HOST,API_KEY)

API_ORDERS_PER_TICK = 100
API_ORDERS_PER_SECOND = 10

EDGE = 0.05
STOCK = "UB"
QUANTITY = 10000

prev_case = None
prev_limits = None
prev_my_orders = None
#prev_other_orders = None

my_orders = {"bids":[], "asks":[]}
other_orders = {"bids":[], "asks":[]}

trader = get_trader()

def get_my_orders(book):
    if book is None or trader is None:
        return {"bids":[],"asks":[]}
    return {"bids":[order for order in book["bids"] if trader["trader_id"] == order["trader_id"]], "asks":[order for order in book["asks"] if trader["trader_id"] == order["trader_id"]]}

def get_other_orders(book):
    if book is None or trader is None:
        return {"bids":[],"asks":[]}
    return {"bids":[order for order in book["bids"] if trader["trader_id"] != order["trader_id"]], "asks":[order for order in book["asks"] if trader["trader_id"] != order["trader_id"]]}

def get_fair_price(book):
    if book is None:
        return None
    #simple halfway between current spread
    #quite naive
    return (max([bid["price"] for bid in book["bids"]])+min(ask["price"] for ask in book["asks"]))/2

counter = 0




fig, (ax1, ax2) = plt.subplots(2, 1)
user_bids = []
user_asks = []

# Plotting histograms
plt.ion()


while True:
    if trader is None:
        trader = get_trader()
    case = get_case()
    if case is None:
        time.sleep(0.5)
        continue
    if prev_case is not None and prev_case["period"] == case["period"] and prev_case["tick"] == case["tick"]:
        time.sleep(0.5)
        continue

    ticker = "UB"

    book = get_security_book(ticker, 10000000)
    news = get_news()

    # only keep orders if the trader id has user in it
    user_bids_and_asks = {}
    user_bids = []
    user_asks = []
    
    
    for i in range(1, 20):
        user_id = "user" + str(i)
        user_bids_and_asks[user_id] = {"bid": None, "ask" : None}
    

    for bid in book["bids"]:
        if "user" in bid["trader_id"]:
            # for i in range(0, int(bid["quantity"])):
            user_bids.extend([bid["price"] for j in range(int(bid["quantity"]))])
            # user_bids.append(bid["price"])
            user_bids_and_asks[bid["trader_id"]]["bid"] = bid

    for ask in book["asks"]:
        if "user" in ask["trader_id"]:
            # for i in range(0, int(ask["quantity"])):
            user_asks.extend([ask["price"] for j in range(int(ask["quantity"]))])
                # user_asks.append(ask["price"])
            user_bids_and_asks[ask["trader_id"]]["ask"] = ask

    # print(user_bids)
    # print(user_asks)
    # print(news)


    """Calculate expected price range given news"""
    lowest_range = 40
    highest_range = 60

    for each_news in news:
        if each_news["news_id"] != 1 and each_news["news_id"] != 7:
            price = float(each_news["body"].split()[-1][1:])
            tick = float(each_news["body"].split()[1])
            local_high = price + (300 - tick)/50
            local_min = price - (300 - tick)/50
            if(local_high < highest_range):
                highest_range = local_high
            if(local_min > lowest_range):
                lowest_range = local_min


    highest_range = round(highest_range,2)
    lowest_range = round(lowest_range,2)

    market_price = get_securities()[0]["last"]

    # print(get_limits())
    current_limit = int(get_limits()[0]["net"])

    """Trade if market price is outside of the range"""
    # if market price < low, buy
    if market_price < lowest_range and current_limit <= (100000 - QUANTITY):
        post_order(ticker=ticker, order_type="LIMIT", quantity=QUANTITY, action="BUY", price=lowest_range - 0.03)
        print("buy order")
    # if market price > high, sell
    if market_price > highest_range and current_limit >= -(100000 - QUANTITY):
        post_order(ticker=ticker, order_type="LIMIT", quantity=QUANTITY, action="SELL", price=highest_range + 0.03)
        print("Sell order")
    

    """Plot Bids and Asks, along with predicted price ranges + market price. """
    ax1.clear()
    ax2.clear()
    fig.tight_layout(pad = 2)
    bins = np.arange(lowest_range - 1, highest_range + 1, 0.25)
    ax1.set_title("Bids")
    ax1.hist(user_bids, bins=bins)
    ax2.set_title("Asks")
    ax2.hist(user_asks, bins=bins)

    ax1.axvline(highest_range, color='r', linewidth=2, label="sell above " + str(highest_range))
    ax1.axvline(lowest_range, color='g', linewidth=2, label="buy below " + str(lowest_range))
    ax1.axvline(get_securities()[0]["last"], color='black', linewidth=2)
    ax2.axvline(highest_range, color='r', linewidth=2, label="sell above " + str(highest_range))
    ax2.axvline(lowest_range, color='g', linewidth=2, label="buy below " + str(lowest_range))
    ax2.axvline(get_securities()[0]["last"], color='black', linewidth=2)

    ax1.legend()

    plt.pause(0.2)



