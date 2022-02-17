#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project -> File   ：worker -> logs
@IDE    ：PyCharm
@Author ：Administrator
@Date   ：2021/7/22 0022 0:08
@Desc   ：
"""
from logging import config
import logconfig

config.dictConfig(logconfig.DEFAULT_LOGGING)