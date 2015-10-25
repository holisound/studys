#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2015-10-09 13:41:39
# @Last Modified by:   edward
# @Last Modified time: 2015-10-25 14:30:33

import MySQLdb
from MySQLdb.cursors import DictCursor
from operator import itemgetter


def sortit(iterable, key=None, reverse=False, conv=iter):
    """
    An alternative to 'sorted' which returns a sorted-iteror instead of a list.
    """
    return conv(sorted(iterable, key=key, reverse=reverse))


def connect(**kwargs):
    """
    A wrapped function based on 'MySQLdb.connect' returns a 'DQL' instance.
    """
    kwargs['cursorclass'] = kwargs.pop('cursorclass', None) or DictCursor
    kwargs['charset'] = kwargs.pop('charset', None) or 'utf8'
    conn = MySQLdb.connect(**kwargs)
    return DQL(conn.cursor())

# ====================


class Storage(dict):

    """
    Originally from 'web.utils' of the 'web.py'
    """

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

    """
    A class as the container of tables' storage.
    """

    def __init__(self, tb_iterable):
        for tb in tb_iterable:
            setattr(self, tb.name, tb)


class Table:

    """
        represents a table in database
    """

    def __init__(self, dql, name, alias=''):
        self.name = name
        self.alias = alias
        self.dql = dql
        self._init_fields()

    def _init_fields(self):
        self.dql.cursor.execute('DESC %s' % self.name)
        fields = ( Field(tb=self, name=r['Field']) for r in self.dql.cursor.fetchall() )
        _field_names = []
        for f in fields:
            setattr(self, f.name, f)
            _field_names.append(f.name)
        self._field_names = sortit(_field_names, conv=tuple)

    def get_fields(self):
        _fields = []
        for name in self._field_names:
            fieldObj = getattr(self, name)
            _field_name = fieldObj.mutation or ( '%s.%s' % (self.alias, name) if self.alias else name )
            _fields.append(_field_name)
        return sortit(_fields, conv=tuple)

    fields = property(get_fields)

    def __repr__(self):
        return '<' + 'name: ' + repr(self.name) + ', alias:' + repr(self.alias) + '>'

    def set_alias(self, alias):
        self.alias = alias


class Field:

    def __init__(self, tb, name):
        self.tb = tb
        self.name = name
        self.mutation = None

    def date_format(self, fmt, alias=''):
        if self.tb.alias and alias:
            mut = 'DATE_FORMAT(%s.%s, %r) AS %s' % (self.tb.alias, self.name, fmt, alias)
        elif self.tb.alias:
            mut = 'DATE_FORMAT(%s.%s, %r)' % (self.tb.alias, self.name, fmt)
        elif alias:
            mut = 'DATE_FORMAT(%s, %r) AS %s' % (self.name, fmt, alias)
        else:
            mut = 'DATE_FORMAT(%s, %r)' % (self.name, fmt)  
        self.mutation = mut
        return mut

class Joint:

    """
        'Joint' abstracts a class to represent the relation to each other between two joined-table.
    """

    def __init__(self, tb, rel):
        """
        tb: Table
        rel: str, 'a=b', 'a.id=b.id'
        """
        self.tb = tb
        self._init_rel(rel)

    def _init_rel(self, rel):
        self.rel = rel.strip()
        self.duplication = self.rel.split('=')[0].strip()

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


INNER_JOIN = lambda tbl: ' INNER JOIN '.join(tbl)


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
        self.joints = []
        self._init_tables()

    def _init_tables(self):
        self.cursor.execute('SHOW TABLES')
        tbl = []
        for name in (r.values()[0] for r in self.cursor.fetchall()):
            tbl.append( Table(dql=self, name=name) )
        self.tables = TableStorage(tbl)

    def get_fields(self):
        if self.maintable is None:
            return ()
        else:
            _fields = []
            _fields.extend(self.maintable.fields)
            for j in self.joints:
                _fields.extend(j.tb.fields)
                # _fields.remove(j.duplication)
            return sortit(_fields, conv=tuple)
    fields = property(get_fields)

    def set_main(self, table, alias=''):
        if isinstance(table, Table) and hasattr(self.tables, table.name):
            self.maintable = table
        elif isinstance(table, basestring) and hasattr(self.tables, table):
            self.maintable = getattr(self.tables, table)
        else:
            raise TypeError(
                "Invalid argument % r, Expect Table or Table.name" % table)
        self.maintable.set_alias(alias)
        return self.maintable

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
        _dql_format = 'SELECT {distinct}{fields} FROM {tables} WHERE {conditions}'
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
        sql = _dql_format.format(
            distinct='DISTINCT ' if distinct else '',
            fields=_fields,
            tables=self._relate(INNER_JOIN) or self.maintable.name,
            conditions=_where_clause,
        )
        print sql
        self.cursor.execute(sql)
        r = self.cursor.fetchall()
        return r

    def inner_join(self, table, on, alias=''):
        if isinstance(table, Table):
            pass
        elif isinstance(table, basestring):
            table = getattr(self.tables, table)
        else:
            raise ValueError("invalid: Support 'str' or 'Table'")
        table.set_alias(alias)
        try:
            assert isinstance(self.maintable, Table)
        except AssertionError:
            raise ValueError(
                "invalid: maintable is not an instance of 'Table'")
        else:
            self.joints.append( Joint(table, on) )

    def _relate(self, method):
        tbl = []
        for j in self.joints:
            f = '{name} AS {alias} ON {rel}' if bool(
                j.tb.alias) is True else '{name} ON {rel}'
            tbl.append(
                f.format(name=j.tb.name, alias=j.tb.alias, rel=j.rel))
        main_f = '{name} AS {alias}' if self.maintable.alias else '{name}'
        main = main_f.format(
            name=self.maintable.name, alias=self.maintable.alias)

        tbl.insert(0, main)
        return method(tbl)


def main():
    # ==========
    # dql = connect(host='localhost', db='QGYM', user='root', passwd='123123')
    # dql.set_main(dql.tables.order_table, 'o')
    dql = connect(host='localhost', db='db', user='root', passwd='123123')
    print dql.fields
    print dql.set_main('student', 'st')
    # print dql.tables.score.sno.date_format()
    print dql.tables.student.sbirthday.date_format('%Y-%m', 'birthday')
    print dql.tables.student.fields
    print dql.fields
    # print dql.set_main(dql.tables.student, 'c')
    # dql.format_field('course_avatar', key=dql.date_format("%m%d"), alias='ca')
    dql.inner_join(dql.tables.score,
                   on='st.sno=cs.sno', alias='cs')
    print dql.fields
    # dql.set_main(dql.tables.score, 'o')
    print dql.fields
    dql.query()
    # print Clause({'a__like': '%as%'}).get_condition_sql()
if __name__ == '__main__':
    main()
