from base import *
from pprint import pprint

class PDBot(BaseBot):

    # If you want to keep track of any information in
    # addition to that stored in BaseBot, feel free to
    # update this init function as necessary.
    def __init__(self):
        super(PDBot, self).__init__()

    qualities = {
        'Buzzfeed': 0.5,
        'The Associated Press': 1.3,
        'Seeking Alpha': 3.5,
        '@ETFGodfather': 0.7
    }

    # Updates the bot's internal state according
    # to trader and market updates from the server.
    # Feel free to modify this method according to how
    # you want to keep track of your internal state.
    def update_state(self, msg):
        super(PDBot, self).update_state(msg)

        # Get the news
        if msg.get('news'):
            news = msg['news']
            source = news['source']
            body = news['body']

            quality = self.qualities[source]
            sd = quality * (600 - self.elapsedTime) / 60

            print "NEWS:", source, ":", body
            print "quality:", quality, "sd:", sd

            estimates = {}

            bodyStocks = body.split('; ')
            for bodyStock in bodyStocks:
                SE = bodyStock.split(' estimated to be worth ')
                stock = SE[0]
                estimate = SE[1]
                estimates[stock] = estimate

            pprint(estimates)

    # Overrides the BaseBot process function.
    # Modify this function if you want your bot to
    # execute a strategy.
    def process(self, msg):
        super(PDBot, self).process(msg)

        return None


if __name__ == '__main__':
    bot = PDBot()
    print "options are", bot.options.data

    for t in bot.makeThreads():
        t.daemon = True
        t.start()

    while not bot.done:
        sleep(0.01)

