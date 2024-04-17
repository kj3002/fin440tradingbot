from rit_api import *
import time
import matplotlib.pyplot as plt
import numpy as np
import statistics
import csv
import threading

"""
    Based on the Rotman Game, Equity Valuation #2
"""


"""Initialize Connection"""
HOST = None
API_KEY = None
if len(sys.argv) < 3:
    HOST = "http://localhost:10001/v1"
    API_KEY = "STWSSJQT"
else:
    HOST = sys.argv[1]
    API_KEY = sys.argv[2]

init(HOST,API_KEY)

prev_case = None
prev_limits = None
prev_my_orders = None

"""Set Constants"""
EDGE = 0.6
TICKER = "BOXX"
QUANTITY = 5000

global Q1_ESTIMATE
global Q2_ESTIMATE
global Q3_ESTIMATE
global Q4_ESTIMATE
Q1_ESTIMATE = 0.5
Q2_ESTIMATE = 0.51
Q3_ESTIMATE = 0.5
Q4_ESTIMATE = 0.51
RISK_FREE_RATE = 0
RISK_PREMIUM = 0.11

MAX_LIMIT = 100000

# last year's dividends
LAST_YEAR_DIVIDENDS = (0.47 + 0.48 + 0.46 + 0.49) * 0.6

# trader = get_trader()

# initialize figure
fig, (ax1, ax2) = plt.subplots(2, 1)
user_bids = []
user_asks = []

# Plotting histograms
plt.ion()


def calculate_estimated_price():
    global ESTIMATE
    R = RISK_FREE_RATE + RISK_PREMIUM
    # print(Q2_ESTIMATE)
    G = (0.6 * (Q1_ESTIMATE + Q2_ESTIMATE + Q3_ESTIMATE + Q4_ESTIMATE))/LAST_YEAR_DIVIDENDS - 1
    ESTIMATE = round( (0.6 * (Q1_ESTIMATE + Q2_ESTIMATE + Q3_ESTIMATE + Q4_ESTIMATE)) / (R - G),2)
    return ESTIMATE
    

def execute_trades():
    global Q1_ESTIMATE
    global Q2_ESTIMATE
    global Q3_ESTIMATE
    global Q4_ESTIMATE

    global RISK_FREE_RATE
    global RISK_PREMIUM
    global QUANTITY
    global EDGE
    global MAX_LIMIT

    print("Starting to Execute trades")

    last_news_size = 1
    while True:
        case = get_case()
        if case is None:
            time.sleep(0.5)
            continue

        if prev_case is not None and prev_case["period"] == case["period"] and prev_case["tick"] == case["tick"]:
            time.sleep(0.5)
            continue

        current_time_tick = case['tick']
        if current_time_tick == 480:
            time.sleep(1)

        # reset estimates if tick = 0
        if current_time_tick == 0:
            Q1_ESTIMATE = 0.5
            Q2_ESTIMATE = 0.51
            Q3_ESTIMATE = 0.5
            Q4_ESTIMATE = 0.51
            RISK_FREE_RATE = 0
            RISK_PREMIUM = 0.11
            # time.sleep(5)
        
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


        securities = get_securities()
        market_price = securities[0]["last"]
        RISK_FREE_RATE = securities[1]["last"]
        
        """Estimate Price based on news + analyst targets"""        
        news = get_news()
        
        if news != None:
            for each_news in reversed(news):
                # print(each_news)
                if each_news["news_id"] == 9 or each_news["news_id"] == 8:
                    Q4_ESTIMATE = float(each_news["body"].split()[-1][1:])
                    # HIGHEST_ESTIMATE = 4

                if each_news["news_id"] == 7 or each_news["news_id"] == 6:
                    Q3_ESTIMATE = float(each_news["body"].split()[-1][1:])
                    # HIGHEST_ESTIMATE = 3
                
                if each_news["news_id"] == 5 or each_news["news_id"] == 4:
                    Q2_ESTIMATE = float(each_news["body"].split()[-1][1:])
                    # HIGHEST_ESTIMATE = 2
                
                if each_news["news_id"] == 3 or each_news["news_id"] == 2:
                    Q1_ESTIMATE = float(each_news["body"].split()[-1][1:])
                    # HIGHEST_ESTIMATE = 1
        
        news_gotten_index = len(news) // 2
        if len(news) == 9:
            news_gotten_index = 5
        elif len(news) == 1:
            news_gotten_index = 0

        # R = RISK_FREE_RATE + RISK_PREMIUM
        # # print(Q2_ESTIMATE)
        # G = (0.6 * (Q1_ESTIMATE + Q2_ESTIMATE + Q3_ESTIMATE + Q4_ESTIMATE))/LAST_YEAR_DIVIDENDS - 1
        # ESTIMATE = round( (0.6 * (Q1_ESTIMATE + Q2_ESTIMATE + Q3_ESTIMATE + Q4_ESTIMATE)) / (R - G),2)
        
        estimated_price = calculate_estimated_price()
    
        highest_range = estimated_price + 0.01
        lowest_range = estimated_price - 0.01
        
        news_gotten_index = len(news) - 1
        
        current_limit = int(get_limits()[0]["net"])
        highest_range = estimated_price + 0.01
        lowest_range = estimated_price - 0.01

        # if just started, don't trade until you get a value
        if news_gotten_index == 0:
            MAX_LIMIT = 0
            EDGE = 100000
        elif news_gotten_index == 1:
            MAX_LIMIT = 10000
            EDGE = 2 * 1.2
        elif news_gotten_index == 3:
            MAX_LIMIT = 20000
            EDGE = 2 * 1
        elif news_gotten_index == 5:
            MAX_LIMIT = 40000
            EDGE = 0.8
        elif news_gotten_index == 7:
            MAX_LIMIT = 100000
            # QUANTITY = 10000
            EDGE = 0.4
        
        # if we have all the information av
        elif news_gotten_index == 8:
            MAX_LIMIT = 100000
            QUANTITY = 10000
            EDGE = 0.02

        # print("Highest Estimate ", str(HIGHEST_ESTIMATE))

        """Trade if market price is outside of the range"""
        # if market price < low, buy
        if market_price < lowest_range - EDGE and current_limit <= (MAX_LIMIT - QUANTITY):
            if news_gotten_index == 8:
                while current_limit <= (MAX_LIMIT - QUANTITY):
                    post_order(ticker=TICKER, order_type="LIMIT", quantity=QUANTITY, action="BUY", price=lowest_range - EDGE)
                    current_limit += QUANTITY
            else:
                post_order(ticker=TICKER, order_type="LIMIT", quantity=QUANTITY, action="BUY", price=lowest_range - EDGE)
            print("buy order at price " + str(lowest_range - EDGE))
            print("Estimated Price " + str(estimated_price))
            print("RF " + str(RISK_FREE_RATE))
        # if market price > high, sell
        if market_price > highest_range + EDGE and current_limit >= -(MAX_LIMIT - QUANTITY):
            if news_gotten_index == 8:
                while current_limit >= -(MAX_LIMIT - QUANTITY):
                    post_order(ticker=TICKER, order_type="LIMIT", quantity=QUANTITY, action="SELL", price=highest_range + EDGE)
                    current_limit -= QUANTITY
            else:
                post_order(ticker=TICKER, order_type="LIMIT", quantity=QUANTITY, action="SELL", price=highest_range + EDGE)
            print("Sell order at price " + str(highest_range + EDGE))
            print("Estimated Price " + str(estimated_price))
            print("RF " + str(RISK_FREE_RATE))
        
        time.sleep(0.1)

def main():
    global Q1_ESTIMATE
    global Q2_ESTIMATE
    global Q3_ESTIMATE
    global Q4_ESTIMATE

    global RISK_FREE_RATE
    global RISK_PREMIUM


    # start trading thread
    t1 = threading.Thread(target=execute_trades)

    t1.start()

    while True:
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
            global Q1_ESTIMATE
            global Q2_ESTIMATE
            global Q3_ESTIMATE
            global Q4_ESTIMATE
            Q1_ESTIMATE = 0.5
            Q2_ESTIMATE = 0.51
            Q3_ESTIMATE = 0.5
            Q4_ESTIMATE = 0.51
            RISK_FREE_RATE = 0
            RISK_PREMIUM = 0.11
        
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


        securities = get_securities()
        market_price = securities[0]["last"]
        RISK_FREE_RATE = securities[1]["last"]
        
        """Estimate Price based on news + analyst targets"""        
        news = get_news()
        
        if news != None:
            for each_news in reversed(news):
                # print(each_news)
                if each_news["news_id"] == 9 or each_news["news_id"] == 8:
                    Q4_ESTIMATE = float(each_news["body"].split()[-1][1:])
                    # HIGHEST_ESTIMATE = 4

                if each_news["news_id"] == 7 or each_news["news_id"] == 6:
                    Q3_ESTIMATE = float(each_news["body"].split()[-1][1:])
                    # HIGHEST_ESTIMATE = 3
                
                if each_news["news_id"] == 5 or each_news["news_id"] == 4:
                    Q2_ESTIMATE = float(each_news["body"].split()[-1][1:])
                    # HIGHEST_ESTIMATE = 2
                
                if each_news["news_id"] == 3 or each_news["news_id"] == 2:
                    Q1_ESTIMATE = float(each_news["body"].split()[-1][1:])
                    # HIGHEST_ESTIMATE = 1
        
        HIGHEST_ESTIMATE = len(news) // 2
        if len(news) == 9:
            HIGHEST_ESTIMATE = 5
        elif len(news) == 1:
            HIGHEST_ESTIMATE = 0

        ESTIMATE = calculate_estimated_price()
        
        highest_range = ESTIMATE + 0.01
        lowest_range = ESTIMATE - 0.01

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
        time.sleep(0.1)



    # Plot histogram
    # t1 = threading.Thread(target=plot_histogram)

    # Execute trades
    # t2 = threading.Thread(target=execute_trades)

    # t1.start()
    # print("starting thread")
    # t1.join()
# t2.start()
# t1.join()
# t2.join()

if __name__ == "__main__":
    main()