#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2015-10-09 13:41:39
# @Last Modified by:   edward
# @Last Modified time: 2015-10-19 23:10:27

import MySQLdb
from MySQLdb.cursors import DictCursor
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


def connect(**kwargs):
    kwargs['cursorclass'] = DictCursor
    kwargs['charset'] = 'utf8'
    conn = MySQLdb.connect(**kwargs)
    return DQL(conn.cursor())

class Table:
    def __init__(self, name, cursor):
        self.name = name
        self.cursor = cursor
    def fields(self):
        self.cursor.execute('SELECT * FROM %s' % self.name)
        r = self.cursor.fetchone()
        return tuple(r.keys())

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
        self.mapping = None
        self._dql = None
        self._init_mapping()
        self._init_tables()
        # self.fields = ()
    def _init_tables(self):
        self.tables = Storage()
        self.cursor.execute('SHOW TABLES')
        for r in self.cursor.fetchall():
            name = r.values()[0]
            setattr(self.tables, name, Table(name, self.cursor))

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
        return tuple(self.mapping.values())
    fields = property(get_fields)

    def get_original_fields(self):
        self._update_fields()
        return tuple(self.mapping.keys())

    def _init_mapping(self):
        if self.maintable is None:
            self.mapping = Storage()
            return
        else:
            if self._dql is None:
                self.cursor.execute('SELECT * FROM %s' % self.maintable.name)
            else:
                self.cursor.execute('SELECT * FROM %s' % self._dql)
        r = self.cursor.fetchone()
        # if self.mapping is None:
        #     self.mapping = Storage()
        for key in r.keys():
            self.mapping.setdefault(key, key)

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
            self.mapping.setdefault(key, key)

    def set_main(self, name, alias=''):
        self.maintable = Storage(name=name, alias=alias)
        self._init_mapping()
        return self.maintable

    def format_field(self, field, key=None):
        if hasattr(self.mapping, field) and key is not None:
            self.mapping[field] = key(field)
        return self.mapping

    def query(self, *args, **kwargs):
        keyword = 'SELECT %s FROM'
        fields = ','.join(i.strip() for i in kwargs.pop('fields', '*'))
        excludes = kwargs.pop('excludes', None)
        if excludes:
            pass

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


def main():
    # ==========
    dql = connect(host='localhost', db='db', user='root', passwd='123123')
    dql.set_main('student', 'st')
    print dql.tables.score.fields()
    print dql.tables.student.fields()
    print dql.mapping


if __name__ == '__main__':
    main()
