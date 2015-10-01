#!/usr/bin/env python
# coding=utf-8
from datetime import date, timedelta, datetime
# dateObj = datetime.strptime('201509', '%Y%m').date()
dateObj = date.today()
def get_target_date(base):
	return lambda d:base + timedelta(days=d)

t_day = get_target_date(dateObj)

date_list = [t_day(i) for i in range(31) if t_day(i).month == t_day(0).month]

def get_filter_by_weekday(wd):
  return lambda d: True if wd == d.isoweekday() else False

sunday = get_filter_by_weekday(1)


ls = [{'a':1},{'a':0}]
lv = [1,2,3,4]
def updatedCopyOfDict(dictObj, **kwargs):
# 新建一个字典的副本，同时可以更新或者添加新的key-value
	from copy import deepcopy
	return deepcopy(dictObj.update(kwargs) or dictObj)


if __name__ == '__main__':
	print map(str, filter(sunday, date_list))
	print [updatedCopyOfDict(s, a=v) for s in ls for v in lv]
