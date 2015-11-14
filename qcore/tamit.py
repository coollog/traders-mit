from base import *
from pprint import pprint

class TAMITBot(BaseBot):

    # If you want to keep track of any information in
    # addition to that stored in BaseBot, feel free to
    # update this init function as necessary.
    def __init__(self):
        super(TAMITBot, self).__init__()

    # Updates the bot's internal state according
    # to trader and market updates from the server.
    # Feel free to modify this method according to how
    # you want to keep track of your internal state.
    def update_state(self, msg):
        super(TAMITBot, self).update_state(msg)

        # Get the new TAMIT data
        if msg.get('news'):
            news = msg['news']
            print "NEWS:", news['headline'], "|", news['source']
            print news['body']

    # Overrides the BaseBot process function.
    # Modify this function if you want your bot to
    # execute a strategy.
    def process(self, msg):
        super(TAMITBot, self).process(msg)

        return None


if __name__ == '__main__':
    bot = TAMITBot()
    print "options are", bot.options.data

    for t in bot.makeThreads():
        t.daemon = True
        t.start()

    while not bot.done:
        sleep(0.01)

