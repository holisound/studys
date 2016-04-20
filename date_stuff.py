# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2016-04-20 10:01:58
# @Last Modified by:   edward
# @Last Modified time: 2016-04-20 11:24:51
from datetime import (
    datetime as dt,
    timedelta)
class DateScope:
    '''
    Date("2012年3月1日", "%Y年%m月%d日") => datetime.datetime(2012, 3, 1, 0, 0)
    Date("2012-03-01", "%Y-%m-%d") => datetime.datetime(2012, 3, 1, 0, 0)
    Date("2012/03/01", "%Y/%m/%d") => datetime.datetime(2012, 3, 1, 0, 0)
    ''' 
    FORMATS = (
        "%Y年%m月%d日",
        "%Y-%m-%d",
        "%Y/%m/%d"
    )
    def __init__(self, date_str=None):
        self.init_datetime(date_str)

    def set_datetime(self, datetime):
        self._datetime = datetime

    @property
    def date(self):
        return self._datetime.date()
    
    def init_datetime(self, date_str):
        if date_str is None:
            self._datetime = dt.now()
        else:
            self._datetime = self.from_datestr(date_str)

    def from_datestr(self, date_str):
        if isinstance(date_str, dt):
            return datestr
        r = None
        for fmt in self.FORMATS:
            try:
                r = dt.strptime(date_str, fmt)
            except ValueError:
                continue
            else:
                return r
        return r


    def filter_of_lastdays(self, days_num, key=None):
        def fn(x):
            if key is not None:
                v = key(x)
            else:
                v = x
            if self.from_datestr(v) is None:
                raise Exception(v)
            date_in = self.from_datestr(v).date()
            return self.date + timedelta(days=1 - days_num) <= date_in <= self.date
        return fn


def main():
    d = DateScope('2012年3月1日')
    print filter(d.FILTER_LASTWEEK, ['2012-3-1', '2012-3-2'])
if __name__ == '__main__':
    main()


