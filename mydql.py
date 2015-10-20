#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2015-10-09 13:41:39
# @Last Modified by:   edward
# @Last Modified time: 2015-10-20 12:22:35

import MySQLdb
from MySQLdb.cursors import DictCursor
from operator import itemgetter


def sortit(iteral, key=None):
    return tuple(sorted(iteral, key=key))


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


def connect(**kwargs):
    kwargs['cursorclass'] = DictCursor
    kwargs['charset'] = 'utf8'
    conn = MySQLdb.connect(**kwargs)
    return DQL(conn.cursor())


class Table:

    def __init__(self, cursor, name, alias=''):
        self.cursor = cursor
        self.name = name
        self.alias = alias

    def __repr__(self):
        return '< ' + 'name: ' + repr(self.name) + ', alias:' + repr(self.alias) + ' >'

    def get_fields(self):
        self.cursor.execute('SELECT * FROM %s' % self.name)
        r = self.cursor.fetchone()
        return sortit(r.keys())
    fields = property(get_fields)

    def set_alias(self, alias):
        self.alias = alias


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
        self.mapping = None
        self._dql = ''
        self._init_mapping()
        self._init_tables()
        # self.fields = ()

    def _init_tables(self):
        self.tables = Storage()
        self.cursor.execute('SHOW TABLES')
        for r in self.cursor.fetchall():
            name = r.values()[0]
            setattr(self.tables, name, Table(name=name, cursor=self.cursor))

    def _init_mapping(self):
        if self.maintable is None:
            self.mapping = Storage()
            return
        else:
            if bool(self._dql) is False:
                self._dql = self.maintable.name
        self.cursor.execute('SELECT * FROM %s' % self._dql)
        r = self.cursor.fetchone()
        for key in r.keys():
            self.mapping.setdefault(key, key)

    def get_fields(self):
        self._init_mapping()
        return sortit(self.mapping.values())
    fields = property(get_fields)

    def get_original_fields(self):
        self._init_mapping()
        return sortit(self.mapping.keys())

    def get_table_names(self):
        return sortit(self.tables.keys())

    def set_main(self, table, alias=''):
        if isinstance(table, Table):
            table.set_alias(alias)
            self.maintable = table
        elif isinstance(table, str):
            self.maintable = Table(self.cursor, table, alias)
        self._init_mapping()
        return self.maintable

    def format_field(self, field, key=None, alias=''):
        if hasattr(self.mapping, field) and key is not None:
            field = key(field)
            if bool(alias) is True:
                field = '%s AS %s' % (field, alias)
            self.mapping[field] = field


    def query(self, *args, **kwargs):
        keyword = 'SELECT %s FROM %s'
        fields = ', '.join(i.strip() for i in self.fields)
        # fields = ','.join(i.strip() for i in kwargs.pop('fields', '*'))
        excludes = kwargs.pop('excludes', None)
        if excludes:
            pass
        sql = keyword % (fields, self._dql)
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
        if bool(self._dql) is False:
            self._dql += ' '.join(
                i.strip() for i in (
                    '%s %s' % (self.maintable.name, 'AS %s' %
                               self.maintable.alias if self.maintable.alias else ''),
                    'INNER JOIN',
                    '%s %s' % (table.name, 'AS %s' %
                               table.alias if table.alias else ''),
                    'ON',
                    on,
                )
            )
        else:
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
    # print isinstance(dql.tables.course_table, Table)
    print dql.set_main(dql.tables.order_table, 'o')
    print dql.fields
    # dql.inner_join(dql.tables.course_schedule_table, on='course_schedule_courseid=course_id', alias='css')
    # dql.inner_join(dql.tables.category_table, on='course_categoryid=category_id', alias='ct')
    dql.format_field('order_date', key=dql.date_format('%Y%m'), alias='order_date')
    print dql.fields
    print dql._dql
    dql.query()

if __name__ == '__main__':
    main()
