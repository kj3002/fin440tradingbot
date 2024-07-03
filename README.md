FIN 440 Trading Algorithms

### Overview
This code is based on trading games from FIN 440, using a variety of methods in order to maximize returns. My performance before creating the algorithms was average to below-average. After, I was consistently in the top 5. Below is some context to some of the games.

### Methodology
The code continuously pings the server for updated information. Note that the program is limited to 100 pings per second, therefore a wait must be added to slow down. In the last game, EV2_bot, two threads were created in order to gain maximum efficiency between displaying data (which takes a very long time), and running the algorithm (which takes very little time).

The code is also very risk averse. We take on positions with high likelihood of success, using math and sometimes taking in various data points to calculate probabilities assuming a relatively normal distribution. This does not, however, guarantee to always get first place, since taking a huge position early on may pay off later.

Visualizations are added to allow the trader to see the current status of the market, and make additional bets. Additionally, if the program seems to be taking wild transactions, the trader can stop the program. 

### Price Discovery (PD)
The price discovery game is as follows: the initial range of prices is between 40 and 60. Throughout the game, an updated price will be given, and given the formula, we can estimate a range to where the actual price is. If the current price is outside the estimated range, the program automatically buys or sell. This means the program cannot lose money, and since the program knows prices and estimates before everyone else, it can also get a better price than others.

### EV1_Bot
This game gives news updates with EPS data. At the end, it will give the final EPS (and therefore final share price amount), and then clear the position in the portfolio.

For this game, data was garnered in order to see general trends in median and standard deviation (see EV1_data.csv). Though not necessarily a "normal distribution", it is reasonable to assume that as more and more EPS data comes in, the standard deviation of the final price of the share gets lower and lower. Therefore, as EPS data comes it, the program calculates the expected price and the ranges given standard deviation. Only until it reaches the last two EPS estimates will the standard deviation go down.

Note that most trades which happen in this program happen in the last minute. This means the program isn't necessarily making money earlier on in the game, thereby being risk averse but also not gaining anything. Therefore, it is up to the trader to make early calls and bets.