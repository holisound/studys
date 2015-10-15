#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: python
# @Date:   2015-10-09 13:41:39
# @Last Modified by:   python
# @Last Modified time: 2015-10-14 11:30:57

import requests
import json

def json_safe_loads(jsonstr, **kwargs):
    try:
        pyObj = json.loads(jsonstr, **kwargs)
    except ValueError:
        pyObj = json.loads(json.dumps(jsonstr), **kwargs)
    finally:
        return pyObj

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
    print kwargs
    print r.text
    jsondict = json_safe_loads(r.text)
    result = jsondict.pop('result', None) if isinstance(jsondict, dict) else jsondict
    res = {'path':abs_path,
            'params': kwargs,
            'response':{
                'result': result,
             }
        }
    if hasattr(jsondict, '__len__') and len(jsondict) > 0:
        key,value = jsondict.popitem()
        res['response']['length'] = len(value) 
        res['response'][key] = value
    r.close()
    return res


def transfer_key_value(dicta, dictb, key):
    return (dicta.get(key) and dictb.setdefault(key, dicta.pop(key))) or \
           (dictb.get(key) and dicta.setdefault(key, dictb.pop(key)))

def copy_dict(dictObj, deep=False, **kwargs):
    """
        'kwargs' collects keyword-arguments to update the copy-content
        if 'deep' is True, recursively-copying will be done.
    """
    if deep:
        from copy import deepcopy
        copyObj = deepcopy(dictObj)
        copyObj.update(kwargs)
    else:
        copyObj = dictObj.copy()
        copyObj.update(kwargs)

    return copyObj
    
class ConditionSQL:

    def __init__(self, dictObj):
        self.dict = self._valid_dict(dictObj)
        self.token_mapping = {
            'eq'   : '= %s',
            'lt'   : '< %s',
            'lte'  : '<= %s',
            'gt'   : '> %s',
            'gte'  : '>= %s',
            'in'   : 'IN (%s)',
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
        return self.dict[key]

    def get_fraction(self, key):
        """
            1. Get single sql-fraction such as 
               'id = 1','id IN (1,2,3)' or 'id >= 5'
            2. While value is of type of str or unicode, the new token will be used instead,
               e.g. city="上海", token '= %s' --> '= "%s"' 
            3. e.g. id__in=(1,) <==> WHERE id IN (1); val = (1,) --> '(1)'
               e.g. id__in=(1,2,3) <==> WHERE id IN (1,2,3); val = (1,2,3) --> '(1,2,3)'
        """
        clean_key = self.get_clean_key(key)
        token = self.get_token(key)
        value = self.get_value(key)
        tail  = self.get_key_tail(key)
        # ==========
        import sys
        major = sys.version_info[0]
        if major == 2:
            typestr = basestring
        elif major == 3:
            typestr = str
        # ==========
        if isinstance(value, typestr):
            token = token % '"%s"'
        elif isinstance(value, (tuple, list)):
            if tail in ('in',):
                value = ','.join(str(i) for i in value)
        return '{key} {condition}'.format(key=clean_key, condition=(token % value))

    def get_condition_sql(self):
        """
            GET Condition-SQL connected with keyword 'AND'
            e.g. ' AND a=1 AND b>2 AND c<10 ...'
        """
        fraction_list = map(self.get_fraction, self.dict)
        # fraction_list.insert(0, '')
        # return ' AND '.join(fraction_list)
        return fraction_list
def valuesOfDictInList(listOfDict):
    """
        [{'a':[1,2]},{'b':[3,4]},{'c':[5,6]}] --> [1,2,3,4,5,6]
    """
    from functools import reduce
    return reduce(lambda x,y:x+y,map(lambda d: d.values(),listOfDict))

def keysOfDictInList(listOfDict):
    """
        [{'a':[1,2]},{'b':[3,4]},{'c':[5,6]}] --> ['a', 'b', 'c']
    """
    return reduce(lambda x,y:x+y,map(lambda d: d.keys(),listOfDict))

class Dictic(dict):

    def get_join(self, key, connector='', reverse=False):
        key, val = str(key), str(self[key])
        frc = (val, key) if reverse else (key, val)
        return connector.join(frc)

    def get_join_gen(self, connector='', reverse=False):
        """
            generator of s which deriving from items 
        """
        return (self.get_join(k, connector, reverse) for k in self.iterkeys())
    # def __getattribute__(self,)

def main():
    a={'a':1, 'b__in':2, 'c__lt':"2012", 'd__lte':22,
    'e__gte':32, 'empty':None, 'id__in':(1, 2, 3), 'ok__range':(1,111),
    'city':'上海',}
    csql = ConditionSQL(a)
    print csql.get_condition_sql()
    d = Dictic(a=1,b=123,c=333)
    # print d.get_join('b','=')
    print list(d.get_join_gen('xxx',True))
if __name__ == '__main__':
    main()
