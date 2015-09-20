# !/usr/bin/env python
# coding=utf-8
import requests
requests.adapters.DEFAULT_RETRIES = 5

from urlparse import urljoin
base_url = 'http://localhost:8080'

def get(rel_path, **kwargs):
    r = requests.request(
        'get',
        urljoin(base_url, rel_path),
        params=kwargs
        )
    res = {'path':rel_path,
            'params': kwargs,
            'response': r.content
            }
    r.close()
    return res

def post(rel_path, **kwargs):
    return requests.request(
        'post',
        urljoin(base_url, rel_path),
        data=kwargs
        )
    res = (rel_path, kwargs, r.status_code, r.content)
    r.close()
    return res



