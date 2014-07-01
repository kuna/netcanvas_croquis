/*
 * netcanvas for croquis
 * by @lazykuna
 * for modified ver of croquis (need overlaylayer - croquis.overlay.js)
 */

var NetCanvas = function(url, croquis) {
	var self = this;
	self.croquis = croquis;

	self.onmessage = function(e) {
		obj = JSON.parse(e.data);
		if (obj["cmd"] == "JOIN") {
			console.log(obj["name"] + " joined");
			self.croquis.addOverlayLayer(obj["name"]);
		} else if (obj["cmd"] == "IMG") {
			console.log("new img from " + obj["name"]);
			var img = new Image();
			img.onload = function () {
				canvas = self.croquis.getOverlayLayer(obj["name"]);
				ctx = canvas.getContext('2d');
				ctx.clearRect(0,0,canvas.width,canvas.height);
			    ctx.drawImage(this, 0, 0);
			}
			img.src = obj["data"];
		} else if (obj["cmd"] == "QUIT") {
			console.log(obj["name"] + " exited");
			self.croquis.removeOverlayLayer(obj["name"]);
		}
	};

	self.onopen = function(e) {

	};

	self.onclose = function(e) {
		// server disconnection
		console.log("connection off.");
	};

	self.onchange = function(e) {
		var canvas = self.croquis.getLayerCanvas(0);
		var data = canvas.toDataURL();	// PNG
		self.wSocket.send(JSON.stringify({"cmd":"IMG", "data":data}));
	};

	self.Disconnect = function() {
		// TODO
		//
		self.wSocket.close();
	};

	if ('WebSocket' in window) {
		self.wSocket = new WebSocket(url);

		// add websocket event handler
		self.wSocket.onmessage = self.onmessage;
		self.wSocket.onopen = self.onopen;
		self.wSocket.onclose = self.onclose;

		// add canvas onchange handler
		self.croquis.addEventListener('onchange', self.onchange);

		console.log("Websocket connected");
	} else {
		console.log("this broswer doesnt support Websocket");
	}
}