#!/usr/bin/env python
#coding=utf-8

import urllib
import re
import random

def get_external_ip():
    pat_ip = re.compile(r'(?:[1-2]?[0-9]+\.){3}[1-2]?[0-9]+')
    # print pat_ip.findall(ip)
    url = random.choice([
        'http://ip.cn',
    ])
    resp = urllib.urlopen(url)

    # print resp.read()
    html = resp.read()
    matches = pat_ip.search(html)
    if matches:
        return matches.group(0)

if __name__ == '__main__':
    print get_external_ip()
