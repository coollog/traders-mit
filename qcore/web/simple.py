from web import *

import sys
sys.path.insert(0, '..')
from base import *
from pprint import pprint

class SimpleBot(BaseBot):
    i = 0

    # If you want to keep track of any information in
    # addition to that stored in BaseBot, feel free to
    # update this init function as necessary.
    def __init__(self):
        super(SimpleBot, self).__init__()

    # Updates the bot's internal state according
    # to trader and market updates from the server.
    # Feel free to modify this method according to how
    # you want to keep track of your internal state.
    def update_state(self, msg):
        super(SimpleBot, self).update_state(msg)

        updateQueue.put(msg)

    # Overrides the BaseBot process function.
    # Modify this function if you want your bot to
    # execute a strategy.
    def process(self, msg):
        super(SimpleBot, self).process(msg)

        orders = [order for order in outputQueue.queue]
        if len(orders) > 0:
            action = {
                'message_type': 'MODIFY ORDERS',
                'orders': orders,
            }
            outputQueue.queue.clear()
            self.sentCount += len(orders)
            print "NEW ORDERS:"
            pprint(action)
            return dumps(action)

        return None


bot = SimpleBot()

if __name__ == '__main__':
    print "options are", bot.options.data

    for t in bot.makeThreads():
        t.daemon = True
        t.start()

    socketio.run(app, port=80)