from rit_api import *
import time

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

    # We have a case and a new tick
    print(f"Period: {case['period']}, Tick: {case['tick']}")


    if case['tick'] == 1:
        post_order("GTT","LIMIT", 10000,"BUY",price=19)
        post_order("GTT","LIMIT", 10000,"BUY",price=19)
        post_order("GTT","LIMIT", 10000,"BUY",price=19)
        post_order("GTT","LIMIT", 10000,"BUY",price=19)
        post_order("GTT","LIMIT", 10000,"BUY",price=19)
    
    # # Only print limits when they change
    # limits = get_limits()
    # if limits != prev_limits:
    #     print(limits)

    # Taking shortcut for this case
    ticker = "GTT"
    print("Before Security Book")
    book = get_security_book(ticker, 10000000)

    # only keep orders if the trader id has user in it
    user_bids_and_asks = {}
    user_bids_and_asks["user1"] = {}

    for bid in book["bids"]:
        if "user" in bid["trader_id"]:
            user_bids_and_asks[bid["trader_id"]]["bid"] = bid

    for ask in book["asks"]:
        if "user" in ask["trader_id"]:
            user_bids_and_asks[ask["trader_id"]]["ask"] = ask

    print(user_bids_and_asks)
    # print(user_asks)
    print("Done printing")

    

    time.sleep(1)

    # print("After Security Book")
    # #print(book)
    # my_orders = get_my_orders(book)
    # #print(my_orders)
    # #cancel all old orders
    # post_cancel_orders(ids=[order["order_id"] for order in my_orders["bids"]])
    # post_cancel_orders(ids=[order["order_id"] for order in my_orders["asks"]])
    # fair_price = get_fair_price(book)
    # if fair_price is None:
    #     continue
    # post_order("HAR","LIMIT",200,"BUY",price=fair_price-EDGE)
    # post_order("HAR","LIMIT",200,"SELL",price=fair_price+EDGE)
    # prev_case = case
    # prev_my_orders = my_orders




