# !/usr/bin/env python
# coding=utf-8
import requests
requests.adapters.DEFAULT_RETRIES = 5

from urlparse import urljoin
base_url = 'http://localhost:8080'

def request(method, rel_path, **kwargs):
    abs_path = base_url + rel_path
    if isinstance(kwargs.get('json'), (dict,)):
        jsonstr = json.dumps(kwargs['json'])
    else:
        jsonstr = kwargs.get('json')
    r = requests.request(
        method,
        abs_path,
        headers = {'json': jsonstr},
        params = kwargs.get('query'),
        )
    jsondict = json.loads(r.text)
    result = jsondict.pop('result')
    res = {'path':abs_path,
            'params': kwargs,
            'response':{
                'result': result,
             }
        }
    if len(jsondict) > 0:
        key,value = jsondict.popitem()
        res['response']['length'] = len(value)
        res['response'][key] = value
    r.close()
    return res

def transfer_key_value(dicta, dictb, key):
    return (dicta.get(key) and dictb.setdefault(key, dicta.pop(key))) or \
           (dictb.get(key) and dicta.setdefault(key, dictb.pop(key)))

def get_condition_string(dictObj):
    def get_clean_key(key):
        if '__' in key:
            key = key.split('__')[0]
        return key 
    def get_token(key):
        token = '='
        if '__' in key:
            tail = key.split('__')[-1]
            if tail == 'lt':
                token = '<'
            elif tail == 'gt':
                token = '>'
            elif tail == 'gte':
                token = '>='
            elif tail == 'lte':
                token = '<='
        return token
    return lambda k: dictObj.get(k) and ' AND {key} {token} "{value}" '.format(
                            key=get_clean_key(k), token=get_token(k), value=dictObj[k])
def get_condition_sql(dictObj):
    get_condition = get_condition_string(dictObj)
    # filter out valid element
    condition_list = filter(
        lambda x:bool(x),
        map(get_condition, dictObj)
        )
    return ''.join(condition_list)

def valuesOfDictInList(listOfDict):
    return reduce(lambda x,y:x+y,map(lambda listOfDict: listOfDict.values(),listOfDict))
def keysOfDictInList(listOfDict):
    return reduce(lambda x,y:x+y,map(lambda listOfDict: listOfDict.keys(),listOfDict))

def main():
    a={'a':1, 'b__gt':2, 'c__lt':10, 'd__lte':22, 'e__gte':32, 'empty':None}
    print get_condition_sql(a)
if __name__ == '__main__':
    main()
