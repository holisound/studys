#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2015-10-11 09:03:41
# @Last Modified by:   edward
# @Last Modified time: 2015-10-12 22:07:34
__metaclass__ = type
import json

class Point:
	def __init__(self, x, y):
		self.x = x
		self.y = y

def serialize(obj):
	d = {'__classname__': type(obj).__name__}
	d.update(vars(obj))
	return d

def unserialize(d):
	clsname = d.pop('__classname__', None)
	if clsname:
		cls = globals()[clsname]
		obj = cls.__new__(cls)
		for (key, val) in d.iteritems():
			setattr(obj, key, val)
		return obj
	else:
		return d
class JSON:
	def __init__(self, d):
		self.__dict__ = d
def main():
	test_dict={'a':4,'b':2,'c':3}
	json_str = json.dumps(test_dict)
	json_obj = json.loads(json_str, object_hook=JSON)
	json_obj.d=123
	print json_obj.a, json_obj.b, json_obj.d

	p = Point(2, 3)
	s = json.dumps(p, default=serialize)
	print s
	a = json.loads(s, object_hook=unserialize)
	print a
	print a.x
	print a.y  

if __name__ == '__main__':
	main()