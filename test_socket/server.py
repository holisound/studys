#!/usr/bin/env python
import socket
s = socket.socket()
host = socket.gethostname()
port = 1234
addr = host, port
s.bind(addr)
s.listen(5)
while 1:
	cs, cs_addr = s.accept()
	print 'Got connection from', cs_addr
	cs.send('Thk U for Connection')
	cs.close()
