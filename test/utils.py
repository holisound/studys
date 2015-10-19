#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: python
# @Date:   2015-10-09 13:41:39
# @Last Modified by:   edward
# @Last Modified time: 2015-10-19 21:46:11

import requests
import json
import MySQLdb
from MySQLdb.cursors import DictCursor
from collections import OrderedDict, deque
from operator import itemgetter

class Storage(dict):

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError, k:
            raise AttributeError, k

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError, k:
            raise AttributeError, k


def json_safe_loads(jsonstr, **kwargs):
    if isinstance(jsonstr, basestring):
        try:
            pyObj = json.loads(jsonstr, **kwargs)
        except ValueError:
            return None
        else:
            return pyObj
    else:
        return jsonstr


def request(method, rel_path, **kwargs):
    abs_path = base_url + rel_path
    if isinstance(kwargs.get('json'), (dict,)):
        jsonstr = json.dumps(kwargs['json'])
    else:
        jsonstr = kwargs.get('json')
    r = requests.request(
        method,
        abs_path,
        headers={'json': jsonstr},
        params=kwargs.get('query'),
    )
    print kwargs
    print r.text
    jsondict = json_safe_loads(r.text)
    result = jsondict.pop('result', None) if isinstance(
        jsondict, dict) else jsondict
    res = {'path': abs_path,
           'params': kwargs,
           'response': {
               'result': result,
           }
           }
    if hasattr(jsondict, '__len__') and len(jsondict) > 0:
        key, value = jsondict.popitem()
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

def connect(**kwargs):
    kwargs['cursorclass'] = DictCursor
    kwargs['charset'] = 'utf8'
    conn = MySQLdb.connect(**kwargs)
    return conn.cursor()

class DQL:
    """
        'DQL' is a simple extension-class based on MySQLdb, 
        which is intended to make convenient-api for satisfying regular DQL-demand.
        it's gotten some features here:
        1. All query-action is starting from 'set_main' which is setted as the maintable.

    """
    def __init__(self, cursor):
        self.cursor = cursor
        self.maintable = None
        self._dql = None
        self.fields_mapping = Storage()
        # self.fields = ()

    # def 
    def query_one(self, sql):
        self.cursor.execute(sql)
        r = self.cursor.fetchone()
        return r

    def query_all(self, sql):
        self.cursor.execute(sql)
        r = self.cursor.fetchall()
        return r

    def get_fields(self):
        self._update_fields()
        return tuple(self.fields_mapping.values())
    fields = property(get_fields)

    def get_original_fields(self):
        self._update_fields()
        return tuple(self.fields_mapping.keys())

    def _update_fields(self):
        if self.maintable is None:
            return {}
        else:
            if self._dql is None:
                self.cursor.execute('SELECT * FROM %s' % self.maintable.name)
            else:
                self.cursor.execute('SELECT * FROM %s' % self._dql)
        r = self.cursor.fetchone()
        for key in r.keys():
            self.fields_mapping.setdefault(key, key)

    def set_main(self, name, alias=''):
        self.maintable = Storage(name=name, alias=alias)
        return self.maintable

    def format_field(self, field, key=None):
        if hasattr(self.fields_mapping, field) and key is not None:
            self.fields_mapping[field] = key(field)
        return self.fields_mapping

    def query(self, *args, **kwargs):
        keyword = 'SELECT %s FROM'
        fields = ','.join(i.strip() for i in kwargs.pop('fields', '*'))
        excludes = kwargs.pop('excludes', None)
        if excludes:pass

        r = super(Connection, self).query(*args, **kwargs)
        return r

    def close_cursor(self):
        self.cursor.close()

    def inner_join(self, name, on, alias=''):   
        self._dql = ' '.join(
            i.strip() for i in (
                '%s %s' % (self.maintable.name, 'AS %s' %
                           self.maintable.alias if self.maintable.alias else ''),
                'INNER JOIN',
                '%s %s' % (name, 'AS %s' % alias if alias else ''),
                'ON',
                on,
            )
        )
        return self._update_fields()

    def get_date_format(self, fmt):
        return lambda field: 'DATE_FORMAT(%s, %r)' % (field, fmt)


class ConditionSQL:

    def __init__(self, dictObj):
        self.dict = self._valid_dict(dictObj)
        self.token_mapping = {
            'eq': '= %s',
            'lt': '< %s',
            'lte': '<= %s',
            'gt': '> %s',
            'gte': '>= %s',
            'in': 'IN (%s)',
            'range': 'BETWEEN %s AND %s'
        }

    def _valid_dict(self, dictObj):
        """
            validate the value of items of dictObj
            if value is 'None' then filter item away
        """
        _filter_func = lambda p: False if p[-1] is None else True
        return dict(filter(_filter_func, dictObj.iteritems()))

    def resolve(self, key):
        """
            'key__tail' --> ('key', 'tail')
            'key'       --> ('key', '')
        """
        ls = key.split('_' * 2)
        length = len(ls)
        if length == 1:
            res = (ls[0], '')
        else:
            res = ls[-2:]
        return tuple(res)

    def get_token(self, tail):
        """
            mapping token by tail, e.g. 'lt', 'eq', 'gt'...
        """
        token = self.token_mapping.get(tail) or self.token_mapping['eq']
        return token

    def get_fraction(self, key):
        """
            1. Get single sql-fraction such as 
               'id = 1','id IN (1,2,3)' or 'id >= 5'
            2. While value is of type of str or unicode, the new token will be used instead,
               e.g. city="上海", token '= %s' --> '= "%s"' 
            3. e.g. id__in=(1,) <==> WHERE id IN (1); val = (1,) --> '(1)'
               e.g. id__in=(1,2,3) <==> WHERE id IN (1,2,3); val = (1,2,3) --> '(1,2,3)'
        """
        ckey, tail = self.resolve(key)
        token = self.get_token(tail)
        value = self.dict[key]
        if isinstance(value, basestring):
            token = token % '"%s"'
            if isinstance(value, unicode):
                value = value.encode("utf-8")
        elif isinstance(value, (tuple, list)):
            if tail in ('in',):
                value = ','.join(str(i) for i in value)
        return '{key} {condition}'.format(key=ckey, condition=(token % value))

    def get_condition_sql(self):
        """
            GET Condition-SQL connected with keyword 'AND'
            e.g. ' AND a=1 AND b>2 AND c<10 ...'
        """
        return 'AND ' + ' AND '.join(self.get_fraction(key) for key in self.dict.iterkeys())


def valuesOfDictInList(listOfDict):
    """
        [{'a':[1,2]},{'b':[3,4]},{'c':[5,6]}] --> [1,2,3,4,5,6]
    """
    from functools import reduce
    return reduce(lambda x, y: x + y, map(lambda d: d.values(), listOfDict))


def keysOfDictInList(listOfDict):
    """
        [{'a':[1,2]},{'b':[3,4]},{'c':[5,6]}] --> ['a', 'b', 'c']
    """
    return reduce(lambda x, y: x + y, map(lambda d: d.keys(), listOfDict))


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


def main():
    # a={'a':1, 'b__in':2, 'c__lt':"2012", 'd__lte':22,
    # 'e__gte':32, 'empty':None, 'id__in':(1, 2, 3), 'ok__range':(1,111),
    # 'city':u'上海','age__gg':33}
    # csql = ConditionSQL(a)
    # print csql.get_condition_sql()
    # d = Dictic(a=1,b=123,c=333)
    # print d.get_join('b','=')
    # print list(d.get_join_gen('xxx',True))
    # print db.get_fileds('student')
    # print db.query_a('student',fields="*", excludes=['sno'])
    # ==========
    cursor = connect(host='localhost', db='db', user='root', passwd='123123')
    dql = DQL(cursor)
    print dql.fields
    dql.set_main('student', alias='st')
    print dql.fields
    dql.inner_join('score', on='st.sno=sc.sno', alias='sc')
    print dql.fields
    f = dql.get_date_format('%M%y')
    dql.format_field('sbirthday', key=f)
    print dql.fields    
    f = dql.get_date_format('%M%y')
    print dql.get_original_fields()
    dql.close_cursor()


if __name__ == '__main__':
    main()
