from Queue import Queue
from time import sleep

from flask import Flask, render_template, send_from_directory
from flask.ext.socketio import SocketIO, emit

from pprint import pprint

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

updateQueue = Queue()
outputQueue = Queue()

@app.route('/')
def index():
    return render_template('web.html')

@app.errorhandler(500)
def handle_internal_error(e):
    return render_template('500.html', error=e), 500

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)


@socketio.on('connect')
def connect():
    emit('connected', {'data': 'Connected'})

@socketio.on('disconnect')
def disconnect():
    print('Client disconnected')

@socketio.on('pull')
def pull():
    msgs = [msg for msg in updateQueue.queue]
    emit('push', msgs)
    updateQueue.queue.clear()

@socketio.on('msg')
def msg(data):
    print data

@socketio.on('buy')
def buy(data):
    ticker = data['ticker']
    quantity = data['n']
    outputQueue.put({
        'ticker': ticker,
        'buy': True,
        'quantity': quantity
    })

@socketio.on('sell')
def sell(data):
    ticker = data['ticker']
    quantity = data['n']
    outputQueue.put({
        'ticker': ticker,
        'buy': False,
        'quantity': quantity
    })