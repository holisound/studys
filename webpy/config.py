#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2016-02-11 16:03:58
# @Last Modified by:   edward
# @Last Modified time: 2016-02-15 21:41:21
import os
if os.getlogin() == 'edward':
  UPLOAD_DIR = "/home/edward/data/www/static/uploads/slide/"
else:
  UPLOAD_DIR = '/home/python/nginx/static/uploads/slide/'