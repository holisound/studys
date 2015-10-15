#!/usr/bin/env python
# coding=utf-8
from datetime import date, timedelta, datetime
import itertools
# dateObj = datetime.strptime('201509', '%Y%m').date()
dateObj = date.today()
def get_target_date(base):
	return lambda d:base + timedelta(days=d)

t_day = get_target_date(dateObj)

date_list = [t_day(i) for i in range(31) if t_day(i).month == t_day(0).month]

def get_filter_by_weekday(wd):
  return lambda d: True if wd == d.isoweekday() else False

sunday = get_filter_by_weekday(1)
def get_date_list(month, weekday):
    dateObj = datetime.strptime(month, "%Y%m").date()
    t_day = get_target_date(dateObj)
    date_gen = (t_day(i) for i in xrange(31) if t_day(i).month == t_day(0).month)
    _filter = get_filter_by_weekday(weekday)
    return [str(i) for i in filter(_filter, date_gen)]

ls = [{'a':1},{'a':0}]
lv = [1,2,3,4]
def updatedCopyOfDict(dictObj, **kwargs):
# 新建一个字典的副本，同时可以更新或者添加新的key-value
    from copy import deepcopy
    return deepcopy(dictObj.update(kwargs) or dictObj)

ls = list(({'month':'201505','day':4},{'month':'201501','day':3},
    {'month':'201505','day':6},{'month':'201510','day':6},{'month':'201511','day':3}))
if __name__ == '__main__':
    def gen(ls):
        # 1st
        ls.sort(key=lambda x:get_date_list(x['month'],x['day'])[0])
        iterObj = itertools.groupby(ls, key=lambda x: x['month'])
        # ===========================
        for key, items in iterObj:
            item_list = list(items)
        # the maximum of identical-weekday of any month is 5
            for i in xrange(5):
                for item in item_list:
                    try:
                        item['date'] = get_date_list(item['month'], item['day'])[i]
                        yield item
                    except IndexError:
                        continue

    g = gen(ls)

    # def gen(x):
    #     for i in xrange(5):
    #         for idx,val in enumerate(x):
    #             try:
    #                 yield get_date_list(val['month'],val['day'])[i]
    #             except IndexError:
    #                 continue
    # g = gen(ls)
    while 1:
        try:
            print g.next()
        except StopIteration:
            break
        
    # print ls
	# print map(str, filter(sunday, date_list))
	# print [updatedCopyOfDict(s, a=v) for s in ls for v in lv]
