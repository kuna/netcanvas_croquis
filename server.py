# -*- coding: utf-8 -*-
# u need tornado library to execute this thing.

from tornado import websocket, web, ioloop, httpserver
import json
import string
import random

class IndexHandler(web.RequestHandler):
	def get(self):
		self.render("netcanvas.htm")

# logined users
# each element consists -
# (connection, name, nick, image)
cl = []

# room info - customize it!
# (canvaswidth, canvasheight)
room = [1024, 600]

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

def informToAll(data):
	for c in cl:
		c[0].write_message(json.dumps(data))

def informToTarget(data, target):
	target.write_message(json.dumps(data))

def informToAllExcept(data, exception):
	for c in cl:
		if (c[0] != exception):
			c[0].write_message(json.dumps(data))

def quitConnection(obj):
	global cl
	target = None
	for c in cl:
		if (c[0] == obj):
			target = c
			break

	if (target == None):
		return

	informToAllExcept({'cmd':"QUIT", 'name':target[1]}, target[0])
	cl = [c for c in cl if c[0] != obj]

class SocketHandler(websocket.WebSocketHandler):
	def open(self):
		if self not in cl:
			newid = id_generator()
			informToTarget({'cmd':"ENTER", 'width':room[0], 'height':room[1]}, self)
			informToAll({'cmd':"JOIN", 'name':newid})
			cl.append([self, newid, None, None])
			# inform about everybody about join
			for c in cl:
				if (c[0] != self):
					informToTarget({'cmd':"JOIN", 'name':c[1]}, self)
			# inform about everybody about nick
			for c in cl:
				if (c[2] != None):
					informToTarget({'cmd':"NICK", 'name':c[1], 'nick':c[2]}, self)
			# inform about everybody about img
			for c in cl:
				if (c[3] != None):
					informToTarget({'cmd':"IMG", 'name':c[1], 'data':c[3]}, self)
			print "new client from", self

	def on_message(self, data):
		# find id of sender
		senderid = None
		sender = None
		for c in cl:
			if (c[0] == self):
				senderid = c[1]
				sender = c
		if (senderid == None):
			print "invalid data from ", self
			return

		ret = json.loads(data);
		if (ret['cmd'] == "IMG"):
			# inform IMG everybody except sender own
			informToAllExcept({'cmd':"IMG", 'name':senderid, 'data':ret['data']}, self)
			# save img data
			sender[3] = ret['data']
			print "received IMG data from", self
		elif (ret['cmd'] == "NICK"):
			# inform NICK everybody except sender own
			informToAllExcept({'cmd':"NICK", 'name':senderid, 'nick':ret['nick']}, self)
			# save nick data
			sender[2] = ret['nick']
			print (self, " changed nick to ", ret['nick'])
		elif (ret['cmd'] == "CHAT"):
			# inform CHAT everybody except sender own
			informToAllExcept({'cmd':"CHAT", 'name':senderid, 'msg':ret['msg']}, self)


	def on_close(self):
		print "closed connection from", self
		quitConnection(self)

def main():
	app = web.Application([
		(r'/', IndexHandler),
		(r'/ws', SocketHandler),
		(r'/(croquis.js)', web.StaticFileHandler, {'path': './'}),
		(r'/(croquis.mobile.js)', web.StaticFileHandler, {'path': './'}),
		(r'/(netcanvas.js)', web.StaticFileHandler, {'path': './'}),
#		(r'/(favicon.ico)', web.StaticFileHandler, {'path': '../'}),
#		(r'/(rest_api_example.png)', web.StaticFileHandler, {'path': './'}),
	])

	http_server = httpserver.HTTPServer(app)
	http_server.listen(8800)
	ioloop.IOLoop.instance().start()

if __name__ == '__main__':
	main()