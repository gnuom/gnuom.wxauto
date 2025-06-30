# -*- coding: utf-8 -*-
import os

# 微信监听群列表
GROUPS_TO_LISTEN = ["wxauto测试", "wxauto测试2", "wxauto测试3", "小团体", "巴啦啦抠脚堡","一家人"]

# 天气API配置
WEATHER_API_KEY = 'ef39706d52464e65a47155b1ac59f87b'
WEATHER_URL = 'https://mh3v58re6v.re.qweatherapi.com/v7/weather/now'
GEO_URL = 'https://mh3v58re6v.re.qweatherapi.com/geo/v2/city/lookup'

# 数据存储路径
CHECKIN_RECORD_DIR = './data/checkin/'
os.makedirs(CHECKIN_RECORD_DIR, exist_ok=True)