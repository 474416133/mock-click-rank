#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project -> File   ：worker -> engine
@IDE    ：PyCharm
@Author ：Administrator
@Date   ：2021/7/21 0021 21:57
@Desc   ：
"""
import random
import logging
from contextlib import contextmanager
import functools
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import settings
logger = logging.getLogger('seo')
try:
    subprocess.Popen = functools.partial(subprocess.Popen, creationflags=subprocess.CREATE_NO_WINDOW)
except:
    pass


@contextmanager
def create_engine():
    """
    :return:
    """
    pc_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36'
    option = Options()
    option.add_argument('--user-agent=%s'% pc_ua)
    option.add_argument('--remote-debugging-port=0')
    if not getattr(settings, 'debug', False):
        option.add_argument('--headless')
        option.add_argument('--disable-gpu')

        prefs = settings.driver['options']['prefs']
        option.add_experimental_option('prefs', prefs)

    # 设置代理
    if settings.proxy_enable:
        proxy_server = 'http://{}'.format(random.choice(settings.ip_proxy_pool))
        print('proxy_server:{}'.format(proxy_server))
        option.add_argument('--proxy-server={}'.format(proxy_server))

    vender = getattr(webdriver, settings.driver['name'])
    driver = vender(settings.driver['driver'], options=option, service_log_path='logs/driver.log')
    try:
        yield driver
    except:
        logger.exception('error!')
    finally:
        driver.quit()

