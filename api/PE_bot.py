from rit_api import *
import time
import matplotlib.pyplot as plt
import numpy as np
import statistics
import csv


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


# def plot_histogram(values, ax, title):
#     plt.hist(values, bins=5)
#     ax.set_xlabel('Categories')
#     ax.set_ylabel('Values')
#     ax.set_title(title)


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

EDGE = 0.6
TICKER = "PI"
QUANTITY = 5000

Q1_ESTIMATE = 0.4
Q2_ESTIMATE = 0.24
Q3_ESTIMATE = 0.27
Q4_ESTIMATE = 0.33

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

    current_time_tick = case['tick']

    # reset estimates if tick = 0
    if current_time_tick == 0:
        Q1_ESTIMATE = 0.4
        Q2_ESTIMATE = 0.24
        Q3_ESTIMATE = 0.27
        Q4_ESTIMATE = 0.33

    
    # print("Before Security Book")

    book = get_security_book(TICKER, 10000000)
    news = get_news()
    
    """Get Bids and Asks to plot"""
    user_bids = []
    user_asks = []

    for bid in book["bids"]:
        if "user" in bid["trader_id"]:
            # for i in range(0, int(bid["quantity"])):
            user_bids.extend([bid["price"] for j in range(int(bid["quantity"]))])

    for ask in book["asks"]:
        if "user" in ask["trader_id"]:
            # for i in range(0, int(ask["quantity"])):
            user_asks.extend([ask["price"] for j in range(int(ask["quantity"]))])

    market_price = get_securities()[0]["last"]

    """Estimate Price based on news + analyst targets"""

    

    estimates_and_earnings = [0] * 8
    
    # if you get news, update the estimate

    # current news id
    current_news_id = 0
    news = get_news()
    print(type(news))
    print(news)
    print(news.reverse())
    
    if news != None:
        for each_news in news:
            print(each_news)
            if each_news["news_id"] == 9 or each_news["news_id"] == 8:
                Q4_ESTIMATE = float(each_news["body"].split()[-1][1:])

            if each_news["news_id"] == 7 or each_news["news_id"] == 6:
                Q3_ESTIMATE = float(each_news["body"].split()[-1][1:])
            
            if each_news["news_id"] == 5 or each_news["news_id"] == 4:
                Q2_ESTIMATE = float(each_news["body"].split()[-1][1:])
            
            if each_news["news_id"] == 3 or each_news["news_id"] == 2:
                Q1_ESTIMATE = float(each_news["body"].split()[-1][1:])
    

    ESTIMATE = round(12.5 * (Q1_ESTIMATE + Q2_ESTIMATE + Q3_ESTIMATE + Q4_ESTIMATE),2)
    
    current_limit = int(get_limits()[0]["net"])
    highest_range = ESTIMATE + 0.01
    lowest_range = ESTIMATE - 0.01

    """Trade if market price is outside of the range"""
    # if market price < low, buy
    if market_price < lowest_range - EDGE and current_limit <= (100000 - QUANTITY):
        post_order(ticker=TICKER, order_type="LIMIT", quantity=QUANTITY, action="BUY", price=lowest_range - EDGE)
        print("buy order")
    # if market price > high, sell
    if market_price > highest_range + EDGE and current_limit >= -(100000 - QUANTITY):
        post_order(ticker=TICKER, order_type="LIMIT", quantity=QUANTITY, action="SELL", price=highest_range + EDGE)
        print("Sell order")

    


    """Plot data and estimates"""
    ax1.clear()
    ax2.clear()
    fig.tight_layout(pad = 2)
    
    
    bins = np.arange(lowest_range - 2, highest_range + 2, 0.25)
    ax1.set_title("Bids")
    ax1.hist(user_bids, bins=bins)
    ax2.set_title("Asks")
    ax2.hist(user_asks, bins=bins)

    # print(get_securities()[0]["last"])
    market_price = get_securities()[0]["last"]
    
    ax1.axvline(highest_range, color='r', linewidth=2, label="sell above " + str(highest_range))
    ax1.axvline(lowest_range, color='g', linewidth=2, label="buy below " + str(lowest_range))
    ax1.axvline(ESTIMATE, color='blue', linewidth=0, label="estimated price " + str(ESTIMATE))
    ax1.axvline(get_securities()[0]["last"], color='black', linewidth=2, label="market price " + str(market_price))
    ax2.axvline(highest_range, color='r', linewidth=2, label="sell above " + str(highest_range))
    ax2.axvline(lowest_range, color='g', linewidth=2, label="buy below " + str(lowest_range))
    ax2.axvline(get_securities()[0]["last"], color='black', linewidth=2, label="market price " + str(market_price))

    ax1.legend()


    plt.pause(0.15)




