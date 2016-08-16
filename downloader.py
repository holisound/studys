#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2016-08-16 08:34:20
# @Last Modified by:   edward
# @Last Modified time: 2016-08-16 14:06:33
from my_algorithms.partition import Partition
import requests
from urlparse import urlparse
from io import BytesIO
import threading
import argparse
import os
import sys


class Master(object):
    def __init__(self, url, worker_num=3, proxy=None):
        self._url = url
        self._proxy = proxy
        self._io_pool = []
        self._content_length = None
        self._finished = 0
        self._percent = 0
        self._initWorkers(worker_num)

    def update_progress(self, size):
        self._finished += size
    def get_progress(self):
        fsh = self._finished
        cln = self.get_content_length()
        p = fsh/float(cln)*100
        if int(p) > self._percent and p < 100:
            self._percent = int(p)
            sys.stdout.write('%02d%%\n' % p)


    def get_proxy(self):
        proxy_uri = self._proxy
        return {urlparse(proxy_uri).scheme: proxy_uri} if proxy_uri else None

    def dump(self, save_path):
        save_path = os.path.split(self._url.split('?')[0])[-1] if save_path is None else save_path
        if os.path.isfile(save_path):
            os.remove(save_path)
        with open(save_path, 'ab') as outf:
            for _, _io in sorted(self._io_pool, key=lambda x: x[0]):
                outf.write(_io.getvalue())

    def add_io(self, io):
        self._io_pool.append(io)

    def get_url(self):
        return self._url

    def get_content_length(self):
        if self._content_length == None:
            clen = requests.head(self._url, proxies=self.get_proxy()).headers['Content-Length']        
            self._content_length = int(clen)
        return self._content_length

    def _initWorkers(self, num):
        self._workers = []
        parts = Partition(self.get_content_length(), num).get_partitions()
        def job(master, bytes_range, pos):
            resp = requests.get(
                url=master.get_url(),
                headers={'Range': 'bytes=%d-%d' % bytes_range},
                proxies=self.get_proxy(),
                stream=True
            )
            bio = BytesIO()
            for block in resp.iter_content(chunk_size=10240):
                bio.write(block)
                master.update_progress(10240)
                master.get_progress()
            master.add_io((pos,bio))

        for i in range(num):
            w = threading.Thread(target=job, args=(self, parts[i], i))
            self._workers.append(w)

    def get_workers(self):
        return self._workers

    def start(self):
        wks = self.get_workers()
        for w in wks:
            w.setDaemon(True)
            w.start()
        for w in wks:
            w.join()

def main():
    parser = argparse.ArgumentParser(description="downloader")
    parser.add_argument('-u', dest='url', required=True, action='store', help="http resource uri")
    parser.add_argument('-w', dest='worker_num', required=False, default=3, action='store', help="how many worker-threads to run")
    parser.add_argument('-x', dest='proxy', required=False, default="socks5://localhost:1080", action="store", help="use proxy(http/socks5)")
    parser.add_argument('-o', dest='outfile', required=False, action="store", help="output file path")
    args = parser.parse_args()
    m = Master(args.url, args.worker_num, args.proxy)
    m.start()
    m.dump(args.outfile)
if __name__ == '__main__':
    main()
