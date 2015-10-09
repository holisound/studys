#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: python
# @Date:   2015-10-09 13:41:39
# @Last Modified by:   edward
# @Last Modified time: 2015-10-09 18:21:24

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
    result = jsondict.pop('result', None)
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

class ConditionSQL:

    def __init__(self, dictObj):
        self.dict = self._valid_dict(dictObj)
        self.token_mapping = {
            'eq'   : '= %s',
            'lt'   : '< %s',
            'lte'  : '<= %s',
            'gt'   : '> %s',
            'gte'  : '>= %s',
            'in'   : 'IN %s',
            'range': 'BETWEEN %s AND %s'
        }
    def _valid_dict(self, dictObj):
        """
            validate the value of items of dictObj
            if value is 'None' then filter item away
        """
        _filter_func = lambda p: False if p[-1] is None else True
        return dict(filter(_filter_func, dictObj.iteritems()))

    def get_clean_key(self, key):
        """
            'key__tail' --> 'key'
        """
        return str(key).split('_'*2)[0]

    def get_key_tail(self, key):
        """
            'key__tail' --> 'tail', others ''
        """
        return str(key).split('_'*2)[-1] if self.is_double_slash_key(key) else ''

    def is_double_slash_key(self, key):
        """
            'key__tail' --> True, others False
        """
        return True if '_'*2 in str(key) else False

    def get_token(self, key):
        """
            mapping token by tail, e.g. lt, eq, gt...
        """
        tail  = self.get_key_tail(key)
        if tail:
            token = self.token_mapping[tail]
        else:
            token = self.token_mapping['eq']
        return token

    def get_value(self, key):
        val = self.dict[key]
        if type(val) is str:
            val = repr(val)
        if str(key).endswith('in') and len(val) == 1:
            return '(%s)' % val[0]
        return val

    def get_sql(self):
        pass

    def get_single(self, key):
        clean_key = self.get_clean_key(key)
        token = self.get_token(key)
        value = self.get_value(key)
        return '{key} {condition}'.format(key=clean_key, condition=(token % value))

    def get_and_sql(self):
        return ' AND '.join(map(self.get_single, self.dict))

def get_condition_string(dictObj):

    return lambda k: dictObj.get(k) and (' AND {key} {token} {value} ' if get_token(k)[-1] in ('in',) else ' AND {key} {token} "{value}" ').format(
                            key=get_clean_key(k), token=get_token(k)[0], value=get_value(k))  

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
    a={'a':1, 'b__gt':2, 'c__lt':"edward", 'd__lte':22, 'e__gte':32, 'empty':None}
    csql = ConditionSQL(a)
    print csql.get_and_sql()
if __name__ == '__main__':
    main()
