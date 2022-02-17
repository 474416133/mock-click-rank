#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project -> File   ：cmdb-sync -> logconfig
@IDE    ：PyCharm
@Author ：Administrator
@Date   ：2021/2/20 0020 9:15
@Desc   ：
"""
import time


LOG_PATH = 'logs'

print('log path: {}'.format(LOG_PATH))
DEFAULT_LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        # 日志格式
        'verbose': {
            'format': '[%(asctime)s] [%(name)s] [%(module)s:%(funcName)s:%(lineno)d] '
                      '[%(levelname)s]- %(message)s'},
        'simple': {  # 简单格式
            'format': '%(message)s'
        },
    },
    # 过滤
    'filters': {
    },
    # 定义具体处理日志的方式
    'handlers': {
        # 默认记录所有日志
        'seo': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '{}/seo.log'.format(LOG_PATH),
            'when': 'D',  # 文件大小
            'backupCount': 5,  # 备份数
            'formatter': 'verbose',  # 输出格式
            'encoding': 'utf-8',  # 设置默认编码，否则打印出来汉字乱码
        },
        'baidu': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '{}/baidu.log'.format(LOG_PATH),
            'when': 'D',  # 文件大小
            'backupCount': 5,  # 备份数
            'formatter': 'verbose',  # 输出格式
            'encoding': 'utf-8',  # 设置默认编码，否则打印出来汉字乱码
        },
        'error': {
            'level': 'ERROR',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '{}/error.log'.format(LOG_PATH),
            'when': 'D',  # 文件大小
            'backupCount': 5,  # 备份数
            'formatter': 'verbose',  # 输出格式
            'encoding': 'utf-8',  # 设置默认编码
        },
        'items': {
                    'level': 'DEBUG',
                    'class': 'logging.handlers.TimedRotatingFileHandler',
                    'filename': '{}/items.log'.format(LOG_PATH),
                    'when': 'D',  # 文件大小
                    'backupCount': 5,  # 备份数
                    'formatter': 'verbose',  # 输出格式
                    'encoding': 'utf-8',  # 设置默认编码，否则打印出来汉字乱码
                },

        # 控制台输出
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    # 配置用哪几种 handlers 来处理日志
    'loggers': {
        # 类型 为 django 处理所有类型的日志， 默认调用
        'seo': {
            'handlers': ['seo', 'error', 'console'],
            'level': 'DEBUG',
            'propagate': False
        },
        # log 调用时需要当作参数传入
        'error': {
            'handlers': ['error'],
            'level': 'ERROR',
            'propagate': False
        },
        'baidu': {
            'handlers': ['baidu', 'error', 'console'],
            'level': 'DEBUG',
            'propagate': False
        },
        'items': {
                    'handlers': ['items'],
                    'level': 'DEBUG',
                    'propagate': False
                },

    }
}