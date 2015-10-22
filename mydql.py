#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2015-10-09 13:41:39
# @Last Modified by:   edward
# @Last Modified time: 2015-10-22 17:22:59

import MySQLdb
from MySQLdb.cursors import DictCursor
from operator import itemgetter


def sortit(iteral, key=None):
    return tuple(sorted(iteral, key=key))


def connect(**kwargs):
    kwargs['cursorclass'] = kwargs.pop('cursorclass', None) or DictCursor
    kwargs['charset'] = kwargs.pop('charset', None) or 'utf8'
    conn = MySQLdb.connect(**kwargs)
    return DQL(conn.cursor())
# ====================


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


class TableStorage:

    def __init__(self, tb_iterable):
        for tb in tb_iterable:
            setattr(self, tb.name, tb)


class Table:

    def __init__(self, cursor, name, alias=''):
        self.cursor = cursor
        self.name = name
        self.alias = alias
        self.fields = self._get_fields()

    def __repr__(self):
        return '<' + 'name: ' + repr(self.name) + ', alias:' + repr(self.alias) + '>'

    def _get_fields(self):
        self.cursor.execute('DESC %s' % self.name)
        return sortit(r['Field'] for r in self.cursor.fetchall())

    def set_alias(self, alias):
        self.alias = alias


class Joint:

    """
        'Joint' abstracts a class to represent the relations to each other between two joined-table.
    """

    def __init__(self, a, b, method):
        setattr(self, a.name, a)
        setattr(self, a.name, b)
        self.method = method


class Clause:

    def __init__(self, dictObj):
        self.dict = self._valid_dict(dictObj)
        self.token_mapping = {
            'eq': '= %s',
            'lt': '< %s',
            'lte': '<= %s',
            'gt': '> %s',
            'gte': '>= %s',
            'in': 'IN (%s)',
            'range': 'BETWEEN %s AND %s',
            'like': 'LIKE %s',
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
        return ' AND '.join(self.get_fraction(key) for key in self.dict.iterkeys())


class DQL:

    """
        'DQL' is a simple extension-class based on MySQLdb, 
        which is intended to make convenient-api for satisfying regular DQL-demand.

    """

    def __repr__(self):
        return 'MyDQL@MySQLdb'

    def __init__(self, cursor):
        self.cursor = cursor
        self.maintable = None
        self.mapping = Storage()
        self._dql = ''
        self._init_tables()

    def _init_tables(self):
        self.cursor.execute('SHOW TABLES')
        _tables = (
            Table(name=r.values()[0], cursor=self.cursor) for r in self.cursor.fetchall())
        self.tables = TableStorage(_tables)

    def _init_mapping(self):
        if self.maintable is None:
            return
        self.cursor.execute('SELECT * FROM %s' %
                            (self._dql or self.maintable.name))
        r = self.cursor.fetchone()
        for key in r.keys():
            self.mapping.setdefault(key, key)

    def get_fields(self):
        return sortit(self.mapping.values())
    fields = property(get_fields)

    def get_original_fields(self):
        return sortit(self.mapping.keys())

    def reset(self):
        self.mapping = Storage()
        self._dql = ''
        self._init_mapping()

    def set_main(self, table, alias=''):
        if isinstance(table, Table):
            table.set_alias(alias)
            self.maintable = table
        elif isinstance(table, str):
            self.maintable = Table(
                cursor=self.cursor, table=table, alias=alias)
        self.reset()
        return self.maintable

    def format_field(self, field, key=None, alias=''):
        if hasattr(self.mapping, field) and key is not None:
            kf = key(field)
            if bool(alias) is True:
                kf = '%s AS %s' % (kf, alias)
            self.mapping[field] = kf

    def query(self, *args, **kwargs):

        """
        fields:
            expect a iterable-object contains names of fields to select
            if not given, defaults to 'self.fields' 
        excludes:
            expect a iterable-object contains names of fields to exclude among 'self.fields'
            if 'fields' argument is given, it would be ignored
        where:
            expect dict-object contains keyword-argument as fitering-condtions

        """
        # distinct
        # or
        # order by desc/asc
        # count
        # subquery
        # avg
        # Aggregation
        # group by
        # having
        # union
        # not
        _dql_format = 'SELECT %s%s FROM %s WHERE %s'
        distinct = kwargs.get('distinct')
        where = kwargs.get('where')
        fields = kwargs.get('fields')
        excludes = kwargs.get('excludes')
        # ==============================
        if fields is None:
            _fields = ', '.join(set(self.fields) - set(excludes or []))
        else:
            _fields = ', '.join(fields or self.fields)
        #
        _where_clause = Clause(where).get_condition_sql() if where else '1=1'
        sql = _dql_format % (
            'DISTINCT ' if distinct else '',
            _fields,
            self._dql or self.maintable.name,
            _where_clause,
        )
        print sql
        self.cursor.execute(sql)
        r = self.cursor.fetchall()
        return r

    def close_cursor(self):
        self.cursor.close()

    def inner_join(self, table, on, alias=''):
        if isinstance(table, Table):
            pass
        elif isinstance(table, str):
            table = getattr(self.tables, table)
        else:
            raise ValueError("invalid: Support 'str' or 'Table'")
        table.set_alias(alias)
        try:
            assert isinstance(self.maintable, Table)
        except AssertionError:
            raise ValueError(
                "invalid: maintable is not an instance of 'Table'")
        # ===================
        # Joint(a, b, 'inner')

        # ===================
        if self._dql is '':
            self._dql += ' '.join(
                i.strip() for i in (
                    '%s %s' % (self.maintable.name, 'AS %s' %
                               self.maintable.alias if self.maintable.alias else ''),
                ))

        self._dql += ' '.join(
            i.strip() for i in (
                '',
                'INNER JOIN',
                '%s %s' % (table.name, 'AS %s' %
                           table.alias if table.alias else ''),
                'ON',
                on,
            )
        )
        self._init_mapping()

    def date_format(self, fmt):
        return lambda field: 'DATE_FORMAT(%s, %r)' % (field, fmt)


def main():
    # ==========
    dql = connect(host='localhost', db='QGYM', user='root', passwd='123123')
    dql.set_main(dql.tables.order_table, 'o')
    print dql.fields
    # dql.format_field(
    #     'order_date', key=dql.date_format('%Y%m'), alias='order_date')
    # print dql.set_main(dql.tables.course_table, 'c')
    # print dql.fields
    # dql.format_field('course_avatar', key=dql.date_format("%m%d"), alias='ca')
    # dql.inner_join(dql.tables.course_schedule_table,
    #                on='course_schedule_courseid=course_id', alias='css')
    # dql.set_main(dql.tables.order_table, 'o')
    # print dql.fields
    # condition = dict(course_id=1)
    # dql.query(where=condition, fields=['course_avatar', 'course_schedule_day'])
    print Clause({'a__like':'%as%'}).get_condition_sql()
if __name__ == '__main__':
    main()
