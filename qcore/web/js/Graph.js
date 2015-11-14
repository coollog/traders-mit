function randomHue() {
  return Math.floor(Math.random() * 256);
}
function randomSat() {
  return Math.floor(Math.random() * 100);
}

var Graph = {
  chart: null,
  start: 0,
  count: 0,
  maxVals: 20,
  series: {},
  lastDraw: 0,
  options: {
    bezierCurve : false,
    datasetStrokeWidth : 1,
    datasetFill : false,
    animation : false,
    pointDot : false,
    showTooltips: false
  },
  pauseDraw: false,
  draw: function () {
    if (this.pauseDraw) return;

    var curTime = new Date().getTime();
    if (curTime - this.lastDraw < 100) return;

    var start = Math.max(0, this.count - this.maxVals);
    var labelCount = Math.min(this.count, this.maxVals);
    var labels = new Array(labelCount);
    for (var i = 0; i < labelCount; i ++) {
      labels[i] = start + i;
    }

    var data = {
      labels: labels,
      datasets: []
    };
    var i = 0;
    for (var label in this.series) {
      if (!this.series[label].show) continue;

      var hue = this.series[label].hue;
      var sat = this.series[label].sat;
      var seriesData = this.series[label].data.slice(start, start + labelCount);
      data.datasets.push({
        label: label,
        strokeColor: "hsla("+hue+","+sat+"%,30%,1)",
        pointColor: "hsla("+hue+","+sat+"%,30%,1)",
        pointStrokeColor: "#fff",
        pointHighlightFill: "#fff",
        pointHighlightStroke: "hsla("+hue+","+sat+"%,30%,1)",
        data: seriesData
      });
    }

    if (data.datasets.length == 0) {
      $('#chart').hide();
      return;
    }

    var ctx = $('#chart').show().get(0).getContext('2d');
    this.chart = new Chart(ctx).Line(data, this.options);

    this.updateTickers();
    this.updateBuyAndSell();

    this.lastDraw = new Date().getTime();
  },
  addDatum: function (label, val) {
    if (!(label in this.series)) {
      this.series[label] = {
        startVal: val,
        data: [0],
        hue: randomHue(),
        sat: randomSat(),
        show: true
      }
    } else {
      var change = 100 * (val - this.series[label].startVal) / this.series[label].startVal;
      this.series[label].data.push(change);

      var len = this.series[label].data.length;
      if (len > this.count) {
        this.count = len;
      }
    }
  },
  setup: function () {
    $('#pausechart').click(function () {
      Graph.pauseDraw = !Graph.pauseDraw;
      if (Graph.pauseDraw) {
        $(this).removeClass('red').html('Unpause Chart');
      } else {
        $(this).addClass('red').html('Pause Chart');
      }
    });
    $('#maxVals').val(Graph.maxVals).change(function () {
      Graph.maxVals = parseInt($(this).val());
    });
  },
  updateTickers: function () {
    for (var label in this.series) {
      var data = this.series[label].data;
      var price = data[data.length - 1] + this.series[label].startVal;
      price = price.toFixed(3);
      var hue = this.series[label].hue;
      var sat = this.series[label].sat;
      var show = this.series[label].show ? '' : 'class="fade"';
      var ticker = $('ticker[label='+label+']');
      if (ticker.size() > 0) {
        ticker.html(label + ': ' + price);
      } else {
        var html =
          '<ticker style="border-color: hsla('+hue+','+sat+'%,30%,1);" label="'+label+'" '+show+'>' + label + ': ' + price +
          '</ticker>';
        $('tickers').append(html);
        $('ticker[label='+label+']').click(function () {
          var label = $(this).attr('label');
          Graph.series[label].show = !Graph.series[label].show;
          console.log(Graph.series[label].show);
          if (Graph.series[label].show) {
            $(this).removeClass('fade');
          } else {
            $(this).addClass('fade');
          }
        });
      }
    }
  },
  updateBuyAndSell: function () {
    var quantity = Trading.quantity;

    for (var label in this.series) {
      if ($('buttongroup[label='+label+']').size() > 0) continue;

      var hue = this.series[label].hue;
      var sat = this.series[label].sat;

      var html = '<buttongroup label="'+label+'">';

      ['buy', 'sell'].forEach(function (type) {
        html +=
          '<button class="'+type+'" quantity="'+quantity+'" label="'+label+'" style="border-color: hsla('+hue+','+sat+'%,30%,1);">' +
            '<'+type+'>'+type.toUpperCase()+'</'+type+'> <quantity>'+quantity+'</quantity> '+label+'</button>';
      });

      html += '<position label="'+label+'"></position></buttongroup>';

      $('buyandsell buttons').append(html);

      $('.buy[label='+label+']').click(function () {
        var label = $(this).attr('label');
        Log.log(label);
        Trading.buy(label);
      });
      $('.sell[label='+label+']').click(function () {
        var label = $(this).attr('label');
        Log.log(label);
        Trading.sell(label);
      });
    }
  }
};

$(Graph.setup);