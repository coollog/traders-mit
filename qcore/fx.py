from base import *

from random import randint

def floatEqual(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

class FXBot(BaseBot):
    case_meta = {
        'endowment':    100000,
        'periods':      3,
        'periodSecs':   900,
        'fees':         0.005, # 50 basis points
        'fines':        0.008, # self-trading
        'limits':       {}
    }

    # If you want to keep track of any information in
    # addition to that stored in BaseBot, feel free to
    # update this init function as necessary.
    def __init__(self):
        super(FXBot, self).__init__()

    def addOrders(self, orders, orderList):
        if len(orders) + len(orderList) >= 25:
            return orders

        quantities = dict.fromkeys(self.positions.keys(), 0)

        overLimit = False
        for order in orders:
            ticker = order['ticker']
            quantity = order['quantity']
            if quantities[ticker] + quantity > 1000:
                overLimit = True
                break
            quantities[ticker] += quantity
        if not(overLimit):
            orders.extend(orderList)

        return orders

    # An example market making strategy.
    # Returns the orders the bots should execute.
    def marketMake(self, orders):
        for ticker, position in self.positions.iteritems():
            lastPrice = self.lastPrices[ticker]

            if abs(position) > self.options.get('position_limit'):
                orders = self.addOrders(orders, [{
                    'ticker': ticker,
                    'buy': position < 0,
                    'quantity': min(1000, abs(position)),
                    'price': lastPrice * (1.5 if position < 0 else 0.5)
                }])
            else:
                if ticker in self.topBid:
                    orders = self.addOrders(orders, [{
                        'ticker': ticker,
                        'buy': True,
                        'quantity': self.options.get('order_quantity'),
                        'price': self.topBid[ticker] + 0.01,
                    }])
                if ticker in self.topAsk:
                    orders = self.addOrders(orders, [{
                        'ticker': ticker,
                        'buy': False,
                        'quantity': self.options.get('order_quantity'),
                        'price': self.topAsk[ticker] - 0.01,
                    }])

        return orders

    # An example momentum strategy.
    # Returns the orders the bot should execute.
    def momentum(self, orders):
        enter_threshold = self.options.get('enter_threshold')
        for ticker, change in self.priceChange.iteritems():
            lastPrice = self.lastPrices[ticker]
            print "MOMENTUM", ticker, ":", lastPrice, "(%.5f)" % change
            if change > enter_threshold:
                orders = self.addOrders(orders, [{
                    'ticker': ticker,
                    'buy': True,
                    'quantity': 100,
                    'price': lastPrice * 1.5,
                }])
            elif change < -enter_threshold:
                orders = self.addOrders(orders, [{
                    'ticker': ticker,
                    'buy': False,
                    'quantity': 100,
                    'price': lastPrice * .5,
                }])

        return orders

    # Triangular arbitrage.
    exchanges = {
        'EUR': {'EUR': 1},
        'USD': {'USD': 1},
        'JPY': {'JPY': 1},
        'CHF': {'CHF': 1},
        'CAD': {'CAD': 1}
    }
    exchangesReady = False

    def getContractCount(self, fromCurr, toCurr, toCount):
        tickers = self.positions.keys()
        ticker = "%s%s" % (fromCurr, toCurr)
        factor = self.exchanges[fromCurr][toCurr]
        count = toCount
        if ticker in tickers:
            count = toCount / factor
        # else:
        #     count = toCount * factor
        count = int(round(count))
        return count

    def getOrder(self, fromCurr, toCurr, quantity):
        tickers = self.positions.keys()
        tickerBuy = "%s%s" % (fromCurr, toCurr)
        tickerSell = "%s%s" % (toCurr, fromCurr)

        if tickerBuy in tickers:
            buy = True
            ticker = tickerBuy
        if tickerSell in tickers:
            buy = False
            ticker = tickerSell

        return {
            'ticker': ticker,
            'buy': buy,
            'quantity': quantity,
            # 'price': self.lastPrices[ticker]
        }

    def calculatePNL(self, orderList):
        profitUSD = 0

        profits = dict.fromkeys(self.exchanges.keys(), 0)

        for order in orderList:
            ticker = order['ticker']
            fromCurr = ticker[3:]
            toCurr = ticker[:3]
            fromAmount = order['quantity'] * self.lastPrices[ticker]
            toAmount = -order['quantity']
            if order['buy']:
                fromAmount *= -1
                toAmount *= -1

            profits[fromCurr] += fromAmount
            profits[toCurr] += toAmount

        # pprint(profits)

        for curr, amount in profits.iteritems():
            profitUSD += amount * self.exchanges[curr]['USD']

        return profitUSD

    def arbitrage(self, orders):
        # Set up exchange graph.
        for ticker, position in self.positions.iteritems():
            lastPrice = self.lastPrices[ticker]

            curr1 = ticker[:3]
            curr2 = ticker[3:]
            self.exchanges[curr1][curr2] = lastPrice
            self.exchanges[curr2][curr1] = 1 / lastPrice
            self.exchangesReady = True

        # Find all triangles in graph.
        # Note that rates go in direction of sell.
        for curr1, edges1 in self.exchanges.iteritems():
            for curr2, edges2 in self.exchanges[curr1].iteritems():
                if curr2 == curr1:
                    continue

                rate12 = self.exchanges[curr1][curr2]
                rate21 = self.exchanges[curr2][curr1]
                for curr3, edges3 in self.exchanges[curr2].iteritems():
                    if curr3 == curr1 or curr3 == curr2:
                        continue
                    if not(curr3 in self.exchanges[curr1]):
                        continue

                    rate23 = self.exchanges[curr2][curr3]
                    rate32 = self.exchanges[curr3][curr2]
                    rate31 = self.exchanges[curr3][curr1]
                    rate13 = self.exchanges[curr1][curr3]

                    overallRate = rate12 * rate23 * rate31
                    if floatEqual(overallRate, 1) or overallRate < 1:
                        continue

                    possibleProfitPerContract = overallRate - 1

                    # Let's say we want to end up with 1000 of curr3.
                    count3 = 100
                    count3 = count3 * self.exchanges['EUR'][curr3]
                    buyRate3 = rate32
                    buyRate2 = rate21
                    sellRate1 = rate13
                    count2 = count3 * buyRate3
                    count1 = count2 * buyRate2

                    # We buy curr2 from curr3, buy curr1 from curr2, and buy
                    # curr3 from curr1.
                    contracts32 = self.getContractCount(curr3, curr2, count2)
                    contracts21 = self.getContractCount(curr2, curr1, count1)
                    contracts13 = self.getContractCount(curr1, curr3, count3)
                    print "CALCULATING ARBITRAGE:", \
                          curr1, curr2, curr3, \
                          count1, count2, count3, \
                          contracts21, contracts32, contracts13
                    if contracts13 < 10 or contracts32 < 10 or contracts21 < 10 or \
                       contracts13 > 1000 or contracts21 > 1000 or contracts32 > 1000:
                       print "EXCEEDED MIN OR MAX ORDER:", contracts32, contracts21, contracts13
                       continue

                    contractCount = contracts32 + contracts21 + contracts13
                    # print count1, count2, count3, contractCount
                    feesUSD = self.case_meta['fees'] * contractCount

                    # # Buy curr2 from curr3
                    order32 = self.getOrder(curr3, curr2, contracts32)
                    # # Buy curr1 from curr2
                    order21 = self.getOrder(curr2, curr1, contracts21)
                    # # Buy curr3 from curr1
                    order13 = self.getOrder(curr1, curr3, contracts13)
                    orderList = [order32, order21, order13]

                    # Calculate our profit.
                    profitUSD = self.calculatePNL(orderList)
                    netProfitUSD = profitUSD - feesUSD

                    # We have an arbitrage opportunity.
                    print "ARBITRAGE ON", curr1, curr2, curr3, \
                          "overallRate:", overallRate, \
                          "profit:", profitUSD, "fees:", feesUSD, "net:", netProfitUSD

                    if netProfitUSD < 0:
                        continue

                    orders = self.addOrders(orders, orderList)

        return orders

    def sellCHFJPY(self):
        ticker = 'CHFJPY'
        orders = 1 * [{
            'ticker': ticker,
            'buy': False,
            'quantity': 100,
            # 'price': self.lastPrices[ticker]
        }]
        return orders

    # Updates the bot's internal state according
    # to trader and market updates from the server.
    # Feel free to modify this method according to how
    # you want to keep track of your internal state.
    def update_state(self, msg):
        super(FXBot, self).update_state(msg)

        # Get position limits of each currency
        if msg.get('case_meta'):
            case_meta = msg['case_meta']
            # pprint(case_meta['currencies'])
            for ticker, props in case_meta['currencies'].iteritems():
                self.case_meta['limits'][ticker] = props['limit']
            print "UPDATED LIMITS:", self.case_meta['limits']

        if msg.get('message_type') == 'TRADER UPDATE' and self.exchangesReady:
            pnlUSD = 0

            # Calculate pnl in USD
            for curr, pnl in self.pnl.iteritems():
                rate = self.exchanges[curr]['USD']
                pnl *= rate
                pnlUSD += pnl

            print "PNL ($)", pnlUSD

    # Overrides the BaseBot process function.
    # Modify this function if you want your bot to
    # execute a strategy.
    def process(self, msg):
        super(FXBot, self).process(msg)

        orders = []

        if (self.started and time() - self.lastActionTime >
                self.options.get('delay')):
            self.lastActionTime = time()

            # XXX: Your strategies go here
            orders = self.marketMake(orders)
            orders = self.momentum(orders)
            orders = self.arbitrage(orders)
            # orders.extend(self.sellCHFJPY())

        if len(orders) > 0:
            action = {
                'message_type': 'MODIFY ORDERS',
                'orders': orders,
            }
            print "NEW ORDERS:"
            pprint(action)
            self.sentCount += len(orders)
            return dumps(action)
        return None


if __name__ == '__main__':
    bot = FXBot()
    print "options are", bot.options.data

    for t in bot.makeThreads():
        t.daemon = True
        t.start()

    while not bot.done:
        sleep(0.01)

