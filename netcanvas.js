/*
 * netcanvas for croquis
 * by @lazykuna
 * for modified ver of croquis (need overlaylayer - croquis.overlay.js)
 * prototype: onNick, onChat, onMessage, onJoin, onQuit, onError, onClose, onOpen, onEnter
 */


var NetCanvas = function(url, croquis, prototype) {
	var self = this;
	self.croquis = croquis;
	self.nick = {};
	self.isconnected = false;
	self.latency = 5000;
	var lastSendTime = 0;
	var ishasSenddata = false;
	var isSending = false;
	if (prototype != null) {
		for (var p in prototype) {
			self[p] = prototype[p];
		}
	}

	self.reconnect = function () {
		if ('WebSocket' in window) {
			self.wSocket = new WebSocket(url);

			// add websocket event handler
			self.wSocket.onmessage = self.onmessage;
			self.wSocket.onopen = self.onopen;
			self.wSocket.onclose = self.onclose;
			self.wSocket.onerror = self.onerror;

			// add canvas onchange handler
			self.croquis.addEventListener('onchanged', self.onchange);

			// should remove all overlay layer in case of reconnecting
			self.croquis.removeOverlayLayer();

			console.log("Websocket connect started");
		} else {
			console.log("this broswer doesnt support Websocket");
		}
	}

	self.getLatency = function () {
		return self.latency;
	};

	self.setLatency = function (l) {
		self.latency = l;
	};


	function isNickExists(nick) {
		for (var id in self.nick) {
			if (self.nick[id] == nick)
				return true;
		}
		return false;
	}

	function getNick(id) {
		return self.nick[id];
	}

	function addNick(id, nick) {
		self.nick[id] = nick;
		console.log(id + " nicknamed as " + nick);
	}

	function removeNick(id) {
		if (self.nick[id] != null)
			delete self.nick[id];
	}

	self.sendData = function(data) {
		// data should be consisted of [cmd], [data]
		if (!self.isconnected) {
			console.log("attempt to send data while its not connected");
			console.log(data);
			return;
		}
		self.wSocket.send(JSON.stringify(data));
	}

	self.onmessage = function(e) {
		obj = JSON.parse(e.data);
		if (obj["cmd"] == "JOIN") {
			console.log(obj["name"] + " joined");
			self.croquis.addOverlayLayer(obj["name"]);
			if (self.onJoin)
				self.onJoin(obj["name"]);
		} else if (obj["cmd"] == "SIZE") {
			console.log("size cmd - width " + obj["width"] + ", height " + obj["height"]);
			self.croquis.setCanvasSize(obj["width"], obj["height"]);
		} else if (obj["cmd"] == "NICK") {
			addNick(obj["name"], obj["nick"])
			if (self.onNick)
				self.onNick(obj["name"], obj["nick"]);
		} else if (obj["cmd"] == "MSG") {
			console.log("message from server - " + obj["msg"]);
			if (self.onMessage)
				self.onMessage(obj["msg"]);
		} else if (obj["cmd"] == "CHAT") {
			var nick = getNick(obj["name"]);
			if (nick == undefined)
				nick = obj["name"];
			console.log("message - " + nick + ", " + obj["msg"]);
			if (self.onChat)
				self.onChat(nick, obj["msg"]);
		} else if (obj["cmd"] == "IMG") {
			if (obj["data"] == "")
				return;
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
			var nick = getNick(obj["name"]);
			if (nick == undefined)
				nick = obj["name"];
			console.log(nick + " exited");
			self.croquis.removeOverlayLayer(obj["name"]);
			if (self.onQuit)
				self.onQuit(nick);
		} else if (obj["cmd"] == "ENTER") {
			console.log("joined!");
			console.log(obj);
			if (self.onEnter)
				self.onEnter(obj["roomname"], obj["width"], obj["height"]);
		}
	};

	self.onopen = function(e) {
		console.log("connected!");
		self.isconnected = true;
		if (self.onOpen)
			self.onOpen();
	};

	self.onclose = function(e) {
		// server disconnection
		console.log("connection off.");
		self.isconnected = false;
		if (self.onClose)
			self.onClose();
	};

	function sendImage() {
		if (isSending) return;

		// check latency
		var ntime = new Date().getTime();
		if (ntime - self.lastSendTime < self.latency) {
			console.log("wont send data under latency");
			if (!ishasSenddata) {
				setTimeout(sendImageDelayed, self.latency - (ntime - self.lastSendTime));
				ishasSenddata = true;
			}
			return;
		}

		var canvas = self.croquis.createFlattenThumbnail();
		var data = canvas.toDataURL();	// PNG
		isSending = true;
		self.sendData({"cmd":"IMG", "data":data});
		isSending = false;
		ishasSenddata = false;
		self.lastSendTime = ntime;
	}
	function sendImageDelayed() {
		if (ishasSenddata) {
			sendImage();
		}
	}
	self.onchange = function(e) {
		sendImage();
	};

	self.reconnect();
}