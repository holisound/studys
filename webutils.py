import web
import os
# 

def make_response(to_response, content_type):
    _filename = to_response;
    web.header('Content-Type', content_type)
    # 
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    # 
    filepath = os.path.join(templates_dir, _filename)
    if os.path.isfile(filepath):
        with open(filepath) as f:
            return f.read()
    else:
        return to_response
# 