from rit_api import *
import time
import matplotlib.pyplot as plt
import numpy as np
import csv

"""Program for getting estimated EPS data. Used for calculating probability distributions for PE Game"""


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
TICKER = "PI"
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


# Name of the CSV file
csv_file = "entry.csv"

# Writing to CSV file
with open(csv_file, mode='w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=['Tick0', 'Q1_Estimate', 'Tick1', 'Q1_Earnings', 'Tick2', 'Q2_Estimate', 'Tick3', 'Q2_Earnings', 'Tick4', 'Q3_Estimate', 'Tick5', 'Q3_Earnings', 'Tick6', 'Q4_Estimate', 'Tick7', 'Q4_Earnings'])
    
    # Write the header
    writer.writeheader()
    

    got_data = False
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


        
        if current_time_tick == 1:
            got_data = False

        estimates_and_earnings = [0] * 8
        ticks = [0] * 8
        news = get_news()

        # print(get_securities())
        market_price = get_securities()[0]["last"]
        r_f = get_securities()[0]["last"]
        
        # reset estimates if tick = 0
        if current_time_tick == 479:

            # read news
            # if you get news, update the estimate
            for news_index in range(0, len(news)):
                print(news)
                # print(news_index)
                if news[news_index]["news_id"] != 1:
                    estimates_and_earnings[8 - news_index - 1] = float(news[news_index]["body"].split()[-1][1:])
                    ticks[8 - news_index - 1] = news[news_index]["tick"]

            # write to csv
            entry = {
                "Tick0" : ticks[0],
                "Q1_Estimate" : estimates_and_earnings[0],
                "Tick1" : ticks[1],
                "Q1_Earnings" : estimates_and_earnings[1],
                "Tick2" : ticks[2],
                "Q2_Estimate" : estimates_and_earnings[2],
                "Tick3" : ticks[3],
                "Q2_Earnings" : estimates_and_earnings[3],
                "Tick4" : ticks[4],
                "Q3_Estimate" : estimates_and_earnings[4],
                "Tick5" : ticks[5],
                "Q3_Earnings" : estimates_and_earnings[5],
                "Tick6" : ticks[6],
                "Q4_Estimate" : estimates_and_earnings[6],
                "Tick7" : ticks[7],
                "Q4_Earnings" : estimates_and_earnings[7]
            }
            # Write the data
            if got_data == False:
                writer.writerow(entry)
                got_data = True
            print(ticks)
            print(f"Wrote Entry!")

        # We have a case and a new tick
        print(f"Period: {case['period']}, Tick: {case['tick']}")
        time.sleep(0.1)




