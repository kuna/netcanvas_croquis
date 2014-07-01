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
cl = []

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

def informToAll(data):
	for c in cl:
		c[0].write_message(json.dumps(data))

def informToTarget(data, target):
	for c in cl:
		if (c[0] == target):
			c[0].write_message(json.dumps(data))
			break

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
			informToAll({'cmd':"JOIN", 'name':newid})
			cl.append([self, newid])
			for c in cl:
				if (c[0] != self):
					informToTarget({'cmd':"JOIN", 'name':c[1]}, self)	# inform all joins
			print "new client from", self

	def on_message(self, data):
		ret = json.loads(data)
		if (ret['cmd'] == "IMG"):
			# find id of sender
			senderid = None
			for c in cl:
				if (c[0] == self):
					senderid = c[1]
			if (senderid == None):
				print "invalid data from", self
				return

			informToAllExcept({'cmd':"IMG", 'name':senderid, 'data':ret['data']}, self)
			print "received IMG data from", self

	def on_close(self):
		print "closed connection from", self
		quitConnection(self)

def main():
	app = web.Application([
		(r'/', IndexHandler),
		(r'/ws', SocketHandler),
		(r'/(croquis.js)', web.StaticFileHandler, {'path': './'}),
		(r'/(netcanvas.js)', web.StaticFileHandler, {'path': './'}),
#		(r'/(favicon.ico)', web.StaticFileHandler, {'path': '../'}),
#		(r'/(rest_api_example.png)', web.StaticFileHandler, {'path': './'}),
	])

	http_server = httpserver.HTTPServer(app)
	http_server.listen(8800)
	ioloop.IOLoop.instance().start()

if __name__ == '__main__':
	main()