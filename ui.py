# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtWidgets import QHeaderView, QSizePolicy, QTabWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from datetime import datetime

import logging
logging.basicConfig(level=logging.DEBUG)


class MessageTableUI(QMainWindow):
    message_received = pyqtSignal(str, str, str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("微信消息监控")
        self.setGeometry(100, 100, 800, 600)

        # 使用 QTabWidget 分组展示不同聊天窗口的消息
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # 存储每个群聊对应的表格
        self.chat_tables = {}

        # 创建主控件和布局
        main_widget = QWidget()
        layout = QVBoxLayout()
        
        # 添加表格区域
        layout.addWidget(self.tabs)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 开始按钮
        self.start_button = QPushButton("开始监听")
        self.start_button.setStyleSheet("QPushButton { background-color: green; color: white; }")
        self.start_button.clicked.connect(self.start_listening)
        
        # 停止按钮
        self.stop_button = QPushButton("停止监听")
        self.stop_button.setStyleSheet("QPushButton { background-color: red; color: white; }")
        self.stop_button.clicked.connect(self.stop_listening)
        self.stop_button.setEnabled(False)
        
        # 状态标签
        self.status_label = QLabel("当前状态：已停止")
        
        # 将按钮添加到布局
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.status_label)
        
        # 清空按钮
        clear_button = QPushButton("清空所有记录")
        clear_button.clicked.connect(self.clear_all_tables)
        
        # 组装布局
        layout.addLayout(button_layout)
        layout.addWidget(clear_button)
        
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        # 初始化线程
        self.worker_thread = None
        
        # 绑定信号 - 使用Qt.QueuedConnection确保跨线程安全
        self.message_received.connect(self.add_message_row, type=Qt.QueuedConnection)
        logging.debug("🔗 UI 信号槽绑定完成")
        
        # 初始更新按钮状态
        self.update_button_states()

    def update_button_states(self):
        """更新按钮状态和样式"""
        is_running = bool(self.worker_thread and self.worker_thread.isRunning())
        
        self.start_button.setEnabled(not is_running)
        self.stop_button.setEnabled(is_running)
        
        if is_running:
            self.status_label.setText("当前状态：运行中")
            self.start_button.setStyleSheet("QPushButton { background-color: lightgray; color: black; }")
            self.stop_button.setStyleSheet("QPushButton { background-color: red; color: white; }")
        else:
            self.status_label.setText("当前状态：已停止")
            self.start_button.setStyleSheet("QPushButton { background-color: green; color: white; }")
            self.stop_button.setStyleSheet("QPushButton { background-color: lightgray; color: black; }")

    def start_listening(self):
        """开始监听"""
        if not self.worker_thread or not self.worker_thread.isRunning():
            logging.info("🔁 开启监听")
            self.worker_thread = WorkerThread(self)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)  # 确保线程完成后清理资源
            self.worker_thread.start()
            self.update_button_states()

    def stop_listening(self):
        """停止监听"""
        if self.worker_thread and self.worker_thread.isRunning():
            logging.info("🛑 停止监听")
            self.worker_thread.stop()
            self.worker_thread.wait()  # 等待线程安全退出
            self.update_button_states()

    def closeEvent(self, event):
        """窗口关闭时清理资源"""
        self.stop_listening()  # 确保关闭时停止监听
        super().closeEvent(event)

    def add_message_row(self, timestamp, chat_who, sender, content):
        logging.debug(f"📊 正在向表格插入数据: {timestamp}, {chat_who}, {sender}, {content}")

        # 如果没有对应tab，则新建一个
        if chat_who not in self.chat_tables:
            table = QTableWidget()
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels(["时间", "发送人", "内容"])
            table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.chat_tables[chat_who] = table
            self.tabs.addTab(table, chat_who)

        table = self.chat_tables[chat_who]
        row_position = table.rowCount()
        table.insertRow(row_position)

        table.setItem(row_position, 0, QTableWidgetItem(timestamp))
        table.setItem(row_position, 1, QTableWidgetItem(sender))
        table.setItem(row_position, 2, QTableWidgetItem(content))

    def clear_all_tables(self):
        for chat_who, table in self.chat_tables.items():
            table.setRowCount(0)
        logging.info("🗑️ 已清空所有消息记录")
    
    def add_message_from_signal(self, msg, chat):
        """处理来自信号的消息，用于跨线程更新UI"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat_who = chat.who
        sender = msg.sender
        content = msg.content
        logging.debug(f"📨 接收到消息: {content} 来自 {chat_who}")
        self.message_received.emit(timestamp, chat_who, sender, content)

class WorkerThread(QThread):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.running = False
        self.listening = False

    def stop(self):
        """安全停止线程"""
        if self.listening:
            from wxauto import WeChat
            wx = WeChat()
            wx.StopListening()
        
        self.running = False
        self.listening = False
        self.quit()
        self.wait()
    
    def run(self):
        try:
            logging.debug("✅ WorkerThread.run() 方法已进入")
            self.running = True
            
            from wxauto import WeChat
            wx = WeChat()

            # 绑定信号到UI更新 - 使用Qt.QueuedConnection确保跨线程安全
            from main import message_handler
            logging.debug("🔔 正在绑定 message_received 信号...")
            message_handler.message_received.connect(self.ui.add_message_from_signal, type=Qt.QueuedConnection)
            logging.debug("🔔 message_received 信号绑定完成")

            from config import GROUPS_TO_LISTEN
            for group in GROUPS_TO_LISTEN:
                logging.info(f"👂 正在监听群聊: {group}")
                wx.AddListenChat(nickname=group, callback=message_handler.handle)

            # 开始监听
            logging.info("🔊 开始监听消息")
            wx.StartListening()
            self.listening = True

            # 进入监听循环
            while self.running:
                self.msleep(1000)  # 避免CPU过载
                
        except Exception as e:
            logging.exception("❌ 执行 WorkerThread.run() 时发生异常", exc_info=True)
        finally:
            self.running = False
            self.listening = False
            logging.info("🧵 线程已退出")

def start_ui():
    logging.debug("🚀 开始启动 PyQt 应用程序")
    app = QApplication(sys.argv)
    window = MessageTableUI()
    window.show()

    thread = WorkerThread(window)
    logging.debug("🧵 正在启动后台线程...")
    thread.start()

    logging.debug("🔁 进入 Qt 主循环...")
    sys.exit(app.exec_())