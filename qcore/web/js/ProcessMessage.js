function processMessages(msgs) {
  msgs.forEach(function (msg) {
    processMessage(msg);
  });
}

function processMessage(msg) {
  if (!('message_type' in msg)) return;

  switch (msg.message_type) {
    case 'TRADER UPDATE': MessageType.traderUpdate(msg); break;
    case 'MARKET UPDATE': MessageType.marketUpdate(msg); break;
    case 'START': Trading.start(); break;
    case 'ACK MODIFY ORDERS': MessageType.orderAck(msg); break;
    case 'NEWS': MessageType.news(msg); break;
  }
}

var MessageType = {
  traderUpdate: function (msg) {
    var state = msg.trader_state;
    var cash = state.cash;
    Trading.positions = state.positions;
    var pnl = state.pnl;
    var totalFees = state.total_fees;
    var totalFines = state.total_fines;
    var totalRebates = state.total_rebates;
    var traderStatus = "Cash " + JSON.stringify(cash) + " PNL " + JSON.stringify(pnl);
    $('traderstatus').html(traderStatus);

    for (var label in Trading.positions) {
      var position = Trading.positions[label];
      $('position[label='+label+']').html(position);
    }
  },
  marketUpdate: function (msg) {
    Trading.start();

    var state = msg['market_state'];
    var ticker = state['ticker'];
    var price = state['last_price'];

    Graph.addDatum(ticker, price);
    Graph.draw();
  },
  orderAck: function (msg) {
    var error = msg.error;
    if (error)
      Log.log('Order error: ' + error, 'red');
    msg.orders.forEach(function (order) {
      if (order.error) {
        Log.log('Order for ' + order.quantity + 'x' + order.ticker + ' errored: ' + order.error, 'red');
      }
    });
  },
  news: function (msg) {
    var headline = msg.news.headline;
    var source = msg.news.source;
    var body = msg.news.body;
    Log.logNews(headline, source, body);

    Trading.processTAMITNews(headline);
  }
};

var Trading = {
  started: false,
  start: function () {
    started = true;
    $('status').addClass('started');
    $('started').html('Started');
  },
  positions: {},
  quantity: 1000,
  buy: function (ticker) {
    socket.emit('buy', {ticker: ticker, n: this.quantity});
  },
  sell: function (ticker) {
    socket.emit('sell', {ticker: ticker, n: this.quantity});
  },
  setup: function () {
    $('#quantity').change(function () {
      Trading.quantity = parseInt($(this).val());
      $('quantity').html(Trading.quantity);
    });
  },
  processTAMITNews: function (headline) {
    var firstSep = '; ';
    var secondSep = ' estimated to be ';

    if (headline.indexOf(secondSep) == -1) return;

    var indicators = {};

    var parts = headline.split(firstSep);
    parts.forEach(function (part) {
      var partSplit = part.split(secondSep);
      indicators[partSplit[0]] = Number(partSplit[1]);
    });

    var tamit = Trading.modelTAMIT(indicators);

    Log.log('TAMIT estimated will be: ' + tamit);
  },
  modelTAMIT: function (indicators) {
    var dx = {};
    var dxx = {};

    for (var indicator in indicators) {
      var val = indicators[indicator];
      var prevVal = Trading.indicatorHist[indicator][Trading.indicatorHist[indicator].length - 1];
      Trading.indicatorHist[indicator].push(val);

      var valPos = val;
      var prevValPos = prevVal;
      switch (indicator) {
        case 'CPI': case 'PPI':
          valPos += 1;
          prevValPos += 1;
          break;
        case 'CCI':
          valPos += 10;
          prevValPos += 10;
          break;
      }

      dx[indicator] = valPos - prevValPos;
      dxx[indicator] = Math.log(valPos) - Math.log(prevValPos);
    }

    var tamit =
      Graph.series['TAMIT'].data[Graph.series['TAMIT'].data.length-1];

    var nextTamit = 0;

    nextTamit += Trading.TAMITModel.tamit * tamit;
    for (var indicator in indicators) {
      nextTamit += Trading.TAMITModel[indicator] * indicators[indicator];
      nextTamit += Trading.TAMITModel[indicator+'dx'] * dx[indicator];
      nextTamit += Trading.TAMITModel[indicator+'dxx'] * dxx[indicator];
    }
    nextTamit += Trading.TAMITModel.one;

    return nextTamit;
  },
  TAMITModel: {
    'tamit': 0.76636028823,
    'GDP': 0.10456676650,
    'CPI': -12.61165234504,
    'GOLD': 0.00744599756,
    'HS': 0.05160599403,
    'PPI': -9.57087202428,
    'ECI': 35.60273229322,
    'CCI': -0.00841882148,
    'MS': -0.00950726574,
    'U': -13.86012562866,
    'GDPdx': 4.86460096819,
    'CPIdx': -11.49093204449,
    'GOLDdx': 0.05730356393,
    'HSdx': 0.11044155826,
    'PPIdx': 198.30148647699,
    'ECIdx': 7318.23213970012,
    'CCIdx': 0.11308287805,
    'MSdx': -0.40548041138,
    'Udx': 3597.06329472886,
    'GDPdxx': -83.50121380020,
    'CPIdxx': 5.86086490877,
    'GOLDdxx': -87.68547234440,
    'HSdxx': -69.25748306523,
    'PPIdxx': -109.37888135851,
    'ECIdxx': -4434.35391990079,
    'CCIdxx': -14.27076824542,
    'MSdxx': 477.02861679403,
    'Udxx': -21569.27233727648,
    'one': 273.42909157811
  },
  indicatorHist: {
    'GDP': [17],
    'CPI': [-0.7],
    'GOLD': [1400],
    'HS': [591],
    'PPI': [-0.5],
    'ECI': [0.6],
    'CCI': [96],
    'MS': [1180],
    'U': [6]
  }
};

$(Trading.setup);