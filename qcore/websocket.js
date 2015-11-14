var WebSocket = require('ws');
var ws = new WebSocket('ws://localhost:10914/trader0/trader0');

ws.on('open', function open () {
  var registerMessage = {
    message_type: "REGISTER",
    token: "kfnwxw29"
  };
  ws.send(JSON.stringify(registerMessage));
});

ws.on('message', function (data, flags) {
  console.log('flags %s', flags.binary);
  console.log('received: %s', data);
});