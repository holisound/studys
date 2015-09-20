# !/usr/bin/python
from . import utils
def test_main():
    reload(utils)    
    
    result = [r for r in (
        utils.get('/'),
        utils.get('greet/'),
        utils.get('greet', name='Edward', age=28),
        utils.get('greet', name='Alice'),
        )]
    return result


