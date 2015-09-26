# !/usr/bin/env python
# coding=utf-8
import requests
requests.adapters.DEFAULT_RETRIES = 5

from urlparse import urljoin
base_url = 'http://localhost:8080'

def get(rel_path, **kwargs):
    r = requests.request(
        'get',
        urljoin(base_url, rel_path),
        params=kwargs
        )
    res = {'path':rel_path,
            'params': kwargs,
            'response': r.content
            }
    r.close()
    return res

def post(rel_path, **kwargs):
    return requests.request(
        'post',
        urljoin(base_url, rel_path),
        data=kwargs
        )
    res = (rel_path, kwargs, r.status_code, r.content)
    r.close()
    return res

def transfer_key_value(dicta, dictb, key):
    return (dicta.get(key) and dictb.setdefault(key, dicta.pop(key))) or \
           (dictb.get(key) and dicta.setdefault(key, dictb.pop(key)))
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
        else:
            token = '='
    
    return token
def get_condition_string(dictObj):
    return lambda k: dictObj.get(k) and ' AND WHERE {key} {token} "{value}" '.format(
                            key=get_clean_key(k), token=get_token(k), value=dictObj[k])
def get_condition_sql(dictObj):
    get_condition = get_condition_string(dictObj)
    return ''.join(get_condition(key) for key in dictObj )
def main():
    a={'a':1}
    print get_condition_sql(a)
if __name__ == '__main__':
    main()
