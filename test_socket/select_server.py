#!/usr/bin/env python
import socket, select

s = socket.socket()
addr = socket.gethostname(), 1234
s.bind(addr)
s.listen(5)
inputs = [s]

while 1:
	rs, ws, es = select.select(inputs, [], [])
	for r in rs:
		if r is s:
			c, addr = s.accept()
			print 'Got connection from', addr
			inputs.append(c)
	else:
		try:
			data = r.recv(1024)
			disconnected = not data
		except socket.error:
			disconnected = True
			
		if disconnected:
			print r.getpeername(), 'disconnected'
			inputs.remove(r)
		else:
			print data