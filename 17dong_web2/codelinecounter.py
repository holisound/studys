#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

exts = ['.py', '.html', '.java', '.xml', '.h', '.m']
def read_line_count(fname):
    count = 0
    character_count = 0
    for file_line in open(fname).xreadlines():
        count += 1
        character_count += len(file_line)
    return (count, character_count)

if __name__ == '__main__':

    line_count = 0
    fcount = 0
    character_count = 0
    for root,dirs,files in os.walk(os.getcwd()):
        for f in files:
            # Check the sub directorys
            fname = (root + '/'+ f).lower()
            try:
                ext = f[f.rindex('.'):]
                if(exts.index(ext) >= 0):
                    fcount += 1
                    (c, cc) = read_line_count(fname)
                    line_count += c
                    character_count += cc
            except:
                pass

    print 'Status ( Web, iOS & Android ):' % exts
    print 'File count: %d' % fcount
    print 'Line count: %d' % line_count
    print 'Character count: %d' % character_count
