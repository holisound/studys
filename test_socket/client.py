#!/usr/bin/env python
import socket

s = socket.socket()
host = socket.gethostname()
port = 1234
addr = host, port
s.connect(addr)
print s.recv(1024)
