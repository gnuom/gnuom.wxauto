# -*- coding: utf-8 -*-
import logging
import os
from datetime import datetime

def setup_logger(log_file='app.log'):
    log_dir = './logs'
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger('WeChatBot')
    logger.setLevel(logging.DEBUG)

    # 控制台输出
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # 文件输出
    fh = logging.FileHandler(os.path.join(log_dir, log_file), encoding='utf-8')
    fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger

logger = setup_logger()