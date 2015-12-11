# -*- coding: utf-8 -*-

"""
Copyright 2013-2015 Win5 Information Technology

@author: Savor d'Isavano
@date: 2015-01-28

The module package.
"""

__author__ = "Savor d'Isavano"

import os

_ENV_PREFIX = '_17DONG_WEB'

env = {
    k[len(_ENV_PREFIX)+1:]: v
    for k, v in os.environ.items() if k.startswith(_ENV_PREFIX)
}
