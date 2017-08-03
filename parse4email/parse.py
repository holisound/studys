# -*- coding: utf-8 -*-
# @Author: wangwh8
# @Date:   2017-08-03 10:53:36
# @Last Modified by:   wangwh8
# @Last Modified time: 2017-08-03 12:18:01
import re
import json

def parse(fpath):
    stat_pat = re.compile(r'\["stats"\] = (.*]]);')
    with open(fpath) as inf:
        html = inf.read()
    fr = stat_pat.findall(html)
    jsonstr = fr[0]
    json_data = json.loads(jsonstr)
    for arr in json_data:
        if len(arr):
            for i in arr:
                if i['label'] == 'Thinkcloud':
                    return ' '.join(str(e) for e in i.values()[1:-1])
def main():
    print parse('./log-20170313-111655.html')
if __name__ == '__main__':
    main()


