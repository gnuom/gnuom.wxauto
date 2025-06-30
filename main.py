# -*- coding: utf-8 -*-
from wxauto import WeChat
from wxauto.msgs import FriendMessage
from logger import logger
from weather import handle_weather_query
from checkin import handle_checkin
from config import GROUPS_TO_LISTEN
from PyQt5.QtCore import pyqtSignal, QObject



class MessageHandler(QObject):
    
    message_received = pyqtSignal(object, object)  # msg, chat

    def __init__(self):
        super().__init__()

    def handle(self, msg, chat):
        logger.info(f"📩 收到消息事件：{msg.content} 来自 {chat.who}")
        self.message_received.emit(msg, chat)
        logger.debug("🔔 已触发 message_received.emit()")

        if isinstance(msg, FriendMessage):
            if '天气' in msg.content:
                handle_weather_query(msg, chat)
            elif msg.content == '打卡':
                logger.debug("🛠️ 正在执行打卡功能")
                handle_checkin(msg, chat)
            else:
                # 示例1：将消息记录到本地文件
                with open('msgs.txt', 'a', encoding='utf-8') as f:
                    f.write(msg.content + '\n')


message_handler = MessageHandler()