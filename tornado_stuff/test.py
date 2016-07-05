from common import BaseHandler as _BaseHandler, fetch_handlers

class BaseHandler(_BaseHandler):
	pass

class Index(BaseHandler):
	url_pattern = '/?'
	def get(self):
	  self.write('Hello,world!\n')

handlers = fetch_handlers(locals(), BaseHandler)
