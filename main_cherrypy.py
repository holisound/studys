#!/usr/bin/env python
#coding=utf-8
import cherrypy as cp
from cherrypy import expose
import json
import test
class HelloWorld(object):

    @expose
    def index(self):
        return json.dumps({'Hello':'World'})

    @expose
    def greet(self,**kwargs):
        name = kwargs.get('name', 'man')
        
        return 'Hello, %s' % name



def main():
    cp.quickstart(HelloWorld())
    
if __name__ == '__main__':
    main()
