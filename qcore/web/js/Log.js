var Log = {
  logging: true,
  log: function (msg, color) {
    if (typeof color === 'undefined') color = 'black';
    $('log')
      .append('<p class="' + color + '">' + msg + '</p>')
      .scrollTop($('log').prop('scrollHeight'));
  },
  setup: function () {
    $('#togglelogging').click(function () {
      Log.logging = !Log.logging;
      if (Log.logging) {
        $(this).addClass('red').html('Pause Logging');
        $('log').removeClass('paused');
      } else {
        $(this).removeClass('red').html('Start Logging');
        $('log').addClass('paused');
      }
    });
  },
  logNews: function (headline, source, body) {
    var color = 'blue';
    this.log(source + ': ' + headline, color);
    this.log(body);
  }
};

$(Log.setup);