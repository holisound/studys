#!/usr/bin/env python
from SocketServer import TCPServer, StreamRequestHandler

class Handler(StreamRequestHandler):
	def handle(self):
		addr = self.request.getpeername()
		print 'Got connection from',  addr
		self.wfile.write('Thk U for connection')
addr = '', 1234
server = TCPServer(addr, Handler)
server.serve_forever()