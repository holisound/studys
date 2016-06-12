def valid_arguments(self):
	r = {}
	for k, v in self.request.arguments.items():
	    if k.startswith('_'): continue
	    v = [ i for i in v if len(i) > 0]
	    if len(v) == 1:
	        tv = v[0]
	    else:
	        tv = ','.join(v)
	    r[k] = tv
	return r
															              v = [ i for i in v if len(i) > 0]
																					              if len(v) == 1:
																										                tv = v
																													               else:
																																                tv = ','.join(v)
																																		             r[k] = tv
																																			           return r
