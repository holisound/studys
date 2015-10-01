#!/usr/bin/env python
# coding=utf-8
from main_cherrypy import HelloWorld, expose, cp
import json
import test

class TestHelloWorld(HelloWorld):

    @expose
    def testit(self):
        return json.dumps(test.main())

def main():
    cp.quickstart(TestHelloWorld(),'/')
if __name__ == '__main__':
    main()