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

def getConnFromClient(c):
	return c[0]

def getNameFromClient(c):
	return c[1]

def getNickFromClient(c):
	return c[2]

def getImageFromClient(c):
	return c[3]

# rooms
# each room has joined client's (name)
# room information(consists) - (roomname, canvaswidth, canvasheight, maxperson, [names])
rooms = []

def roomExists(roomname):
	return (getRoom(roomname) != None)

def getRoom(roomname):
	for r in rooms:
		if (r[0] == roomname):
			return r
	return None

def roomCreate(roomname, width, height):
	try:
		tw = int(width)
		th = int(height)

		if (tw < 0 or th < 0):
			return False

		if (tw > 1280 or th > 800):
			return False

		rooms.append([roomname, width, height, 5, []])
		return True
	except:
		return False

def getRoomnameFromName(name):
	for r in rooms:
		names = r[4]
		for n in names:
			if (n == name):
				return r[0]
	return None

def getClientsFromRoomname(roomname):
	ret = []
	for r in rooms:
		if (len(ret) > 0):
			break
		if (r[0] == roomname):
			names = r[4]
			for c in cl:
				if (c[1] in names):
					ret.append(c)
	return ret

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

def informToAll(roomname, data):
	rcl = getClientsFromRoomname(roomname)
	for c in rcl:
		c[0].write_message(json.dumps(data))

def informToTarget(data, target):
	#print data
	target.write_message(json.dumps(data))

def informToAllExcept(roomname, data, exception):
	rcl = getClientsFromRoomname(roomname)
	for c in rcl:
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

	name = target[1]
	roomname = getRoomnameFromName(name)
	if (roomname != None):
		# inform to all about exiting
		informToAllExcept(roomname, {'cmd':"QUIT", 'name':name}, target[0])
		# reset room info (automatically exit)
		i = 0
		for r in rooms:
			if (name in r[4]):
				r[4].remove(name)
				#rooms[i] = r
				if (len(r[4]) == 0):
					del rooms[i]
					i -= 1
			i += 1

	# remove from client info
	cl = [c for c in cl if c[0] != obj]


class SocketHandler(websocket.WebSocketHandler):
	def open(self):
		if self not in cl:
			newid = id_generator()
			cl.append([self, newid, None, None])
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
			# get room name
			roomname = getRoomnameFromName(senderid)
			if (roomname == None):
				print "IMG error - no roomname"
				return
			# inform IMG everybody except sender own
			informToAllExcept(roomname, {'cmd':"IMG", 'name':senderid, 'data':ret['data']}, self)
			# save img data
			sender[3] = ret['data']
			print "received IMG data from", self
		elif (ret['cmd'] == "NICK"):
			# get room name
			roomname = getRoomnameFromName(senderid)
			if (roomname == None):
				print "NICK error - no roomname"
				return
			# inform NICK everybody except sender own
			informToAllExcept(roomname, {'cmd':"NICK", 'name':senderid, 'nick':ret['nick']}, self)
			# save nick data
			sender[2] = ret['nick']
			print (self, " changed nick to ", ret['nick'])
		elif (ret['cmd'] == "CHAT"):
			# get room name
			roomname = getRoomnameFromName(senderid)
			if (roomname == None):
				print "CHAT error - no roomname"
				return
			# inform CHAT everybody except sender own
			informToAllExcept(roomname, {'cmd':"CHAT", 'name':senderid, 'msg':ret['msg']}, self)
		elif (ret['cmd'] == "ENTER"):
			# TODO: is room exists?
			r = getRoom(ret['roomname'])
			if (r == None):
				informToTarget({'cmd':'MSG', 'msg':'no room such name!'}, self)
				return
			# TODO: if over maxpeople, send "full capacity" message.
			if (len(r[4]) == r[3]):
				informToTarget({'cmd':'MSG', 'msg':'full room!'}, self)
				return
			# TODO: inform join to self
			print "ENTER", sender
			self.joinRoom(sender, r)
		elif (ret['cmd'] == "CREATE"):
			# TODO: is room exists?
			if (roomExists(ret['roomname'])):
				informToTarget({'cmd':'MSG', 'msg':'already exists!'}, self)
				return
			# TODO: if not exists, then create
			if (not roomCreate(ret['roomname'], ret['width'], ret['height'])):
				informToTarget({'cmd':'MSG', 'msg':'error occured during creating room'}, self)
				return
			# TODO: inform join to self
			r = getRoom(ret['roomname'])
			self.joinRoom(sender, r)

	def on_close(self):
		print "closed connection from", self
		quitConnection(self)

	def joinRoom(self, c, room):
		# inform to everybody that I joined except me
		print c
		informToAllExcept(room[0], {'cmd':"JOIN", 'name':c[1]}, c[0])

		# get information of room (canvas size)
		print c
		informToTarget({'cmd':"ENTER", 'roomname':room[0], 'width':room[1], 'height':room[2]}, c[0])
		rname = room[4]
		rcl = []
		for c__ in cl:
			if (c__[1] in rname):
				rcl.append(c__)
		# get information of everybody about join
		for c_ in rcl:
			if (c_[0] != c[0]):
				informToTarget({'cmd':"JOIN", 'name':c_[1]}, c[0])
		# get information of everybody about nick
		for c_ in rcl:
			if (c_[2] != None):
				informToTarget({'cmd':"NICK", 'name':c_[1], 'nick':c_[2]}, c[0])
		# get information of everybody about img
		for c_ in rcl:
			if (c_[3] != None):
				informToTarget({'cmd':"IMG", 'name':c_[1], 'data':c_[3]}, c[0])

		# add me into the room!
		room[4].append(getNameFromClient(c));
		print "client ", self, " joined ", room[0]

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