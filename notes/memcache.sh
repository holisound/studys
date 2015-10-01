#!/bin/sh
#step 1st - installation
sudo apt-get install libevent-dev
sudo apt-get install memcached
#1
pip install python-memcache
#2
sudo apt-get install python-dev libmemcached-dev
pip install pylibmc

#启动 memcache 
memcache
#默认端口11211

