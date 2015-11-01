#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2015-10-09 13:41:39
# @Last Modified by:   edward
# @Last Modified time: 2015-11-02 00:10:46
__metaclass__ = type
from MySQLdb.cursors import DictCursor
from MySQLdb.connections import Connection


def sortit(iterable, key=None, reverse=False, conv=iter):
    """
    An alternative to 'sorted' which returns a sorted-iteror instead of a list.
    """
    return conv(sorted(iterable, key=key, reverse=reverse))


def connect(**kwargs):
    """
    A wrapped function based on 'MySQLdb.connections.Connection' returns a 'Connection' instance.
    """
    kwargs['cursorclass'] = kwargs.pop('cursorclass', None) or DictCursor
    kwargs['charset'] = kwargs.pop('charset', None) or 'utf8'
    return DataBase(**kwargs)

# ====================


class Storage(dict):

    """
    A Storage object is like a dictionary except `obj.foo` can be used
    in addition to `obj['foo']`.

        >>> o = storage(a=1)
        >>> o.a
        1
        >>> o['a']
        1
        >>> o.a = 2
        >>> o['a']
        2
        >>> del o.a
        >>> o.a
        Traceback (most recent call last):
            ...
        AttributeError: 'a'

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

    def __repr__(self):
        return '<Storage ' + dict.__repr__(self) + '>'

class FieldStorage(set):
    pass

class DataBase(Connection):

    def __init__(self, **kwargs):
        super(DataBase, self).__init__(**kwargs)
        self._init_tables()

    def _init_tables(self):
        cursor = self.cursor()
        cursor.execute('SHOW TABLES')
        self.tables = Storage()
        for name in (r.values()[0] for r in cursor.fetchall()):
            self.tables[name] = Table(db=self, name=name)

    def GetTable(self, name):
        return self.tables[name]

    def GetTableByFieldName(self, fieldname):
        for table in self.tables.itervalues():
            if fieldname in table.fields:
                return table

    def GetField(self, tablename, fieldname):
        return self.tables[tablename].fields[fieldname]

    def DQL(self):
        return _DQL(self)


class Table:

    """
        represents a table in database
    """

    def __init__(self, db, name, alias=''):
        self.name = name
        self.alias = alias
        self.db = db
        self._init_fields()

    def _init_fields(self):
        cursor = self.db.cursor()
        cursor.execute('DESC %s' % self.name)
        fields = (Field(tb=self, name=r['Field'])
                  for r in cursor.fetchall())
        self.fields = fs = Storage()
        for f in fields:
            fs[f.name] = f

    def get_fields(self):
        return sortit(self.fields, conv=set)

    FieldNames = property(get_fields)

    def __repr__(self):
        return '<type: %r, name: %r, alias: %r>' % (self.__class__.__name__, self.name, self.alias)

    def set_alias(self, alias):
        self.alias = alias


class Field:

    def __init__(self, tb, name):
        self.tb = tb
        self.name = name
        self.mutation = None

    def date_format(self, fmt, alias=''):
        if self.tb.alias:
            mut = 'DATE_FORMAT(%s.%s, %r) AS %s' % (
                self.tb.alias, self.name, fmt, alias or self.name)
        else:
            mut = 'DATE_FORMAT(%s, %r) AS %s' % (
                self.name, fmt, alias or self.name)
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

    def __init__(self, dql, dictObj):
        self.dql = dql
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
        # ckey is equivalent to fieldname
        # access corresponding table by fieldname

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


class _DQL:

    """
        '_DQL' is a simple extension-class based on MySQLdb, 
        which is intended to make convenient-api for satisfying regular DQL-demand.

    """

    def __enter__(self): return self

    def __exit__(self, exc, value, tb): self.db.close()

    def __repr__(self): return 'MyDQL@MySQLdb'

    def __init__(self, db):
        self.db = db
        self.maintable = None
        self.joints = []
        # self._init_tables()

    # def _init_tables(self):
    #     self.db.cursor().execute('SHOW TABLES')
    #     tbl = []
    #     for name in (r.values()[0] for r in cursor.fetchall()):
    #         tbl.append(Table(dql=self, name=name))
    #     self.tables = Store(tbl)

    def get_fields(self):
        fs = FieldStorage()
        if self.maintable is not None:
            fs.update(self.maintable.FieldNames)
            for j in self.joints:
                fs.update(j.tb.FieldNames)
        return fs
    fields = property(get_fields)

    def set_main(self, tablename, alias=''):
        """
        'table' expects Table.name
        """
        _table = getattr(self.db.tables, tablename)
        try:
            assert isinstance(_table, Table)
        except AssertionError:
            raise TypeError("%r is not an instance of 'Table'" % _table)
        else:
            _table.set_alias(alias)
            self.maintable = _table
            return _table

    def get_dql(self, *args, **kwargs):
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
        _where_clause = Clause(
            self, where).get_condition_sql() if where else '1=1'
        _dql = _dql_format.format(
            distinct='DISTINCT ' if distinct else '',
            fields=_fields,
            tables=self._relate(INNER_JOIN),
            conditions=_where_clause,
        )
        return _dql

    def create_view(self, name, *args, **kwargs):
        self.db.cursor().execute('CREATE OR REPLACE VIEW {name} AS {dql} '.format(
            name=name, dql=self.get_dql(*args, **kwargs)))
        _view = Table(db=self.db, name=name)
        setattr(self.db, name, _view)
        return _view

    def query(self, *args, **kwargs):
        cursor = self.db.cursor()
        cursor.execute(self.get_dql(*args, **kwargs))
        return cursor.fetchall()

    def queryone(self, *args, **kwargs):
        cursor = self.db.cursor()
        cursor.execute(self.get_dql(*args, **kwargs))
        return cursor.fetchone()

    def inner_join(self, table, on, alias=''):
        if isinstance(table, Table):
            pass
        elif isinstance(table, basestring):
            table = getattr(self.tables, table)
        else:
            raise ValueError("invalid: Support 'str' or 'Table'")
        table.set_alias(alias)
        #
        try:
            assert isinstance(self.maintable, Table)
        except AssertionError:
            raise ValueError(
                "invalid: maintable is not an instance of 'Table'")
        else:
            self.joints.append(Joint(table, on))
        finally:
            return table

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
    db = connect(host='localhost', db='db', user='root', passwd='123123')
    dql = db.DQL()
    print dql.fields
    print dql.set_main('student', 'st')

    # print dql.get_dql()
    # dql.query()
    print db.GetField('student', 'sbirthday').date_format('%Y-%m', 'birthday')
    # print dql.db.tables.student.fields.sbirthday.date_format('%Y-%m', 'birthday')

    # print dql.tables.student.fields
    # print dql.fields
    # print dql.set_main(dql.tables.student, 'c')
    # dql.format_field('course_avatar', key=dql.date_format("%m%d"), alias='ca')
    # dql.inner_join(dql.tables.score,
    #                on='st.sno=cs.sno', alias='cs')
    # print dql.fields
    # dql.set_main(dql.tables.score, 'o')
    # print dql.fields
    # dql.query()
    # print Clause({'a__like': '%as%'}).get_condition_sql()
if __name__ == '__main__':
    main()
