import time
import tkinter as tk
from tkinter import ttk
import logging
from datetime import datetime
from collections import deque
from threading import Lock

class Logger:
    _instance = None
    MAX_CACHE_SIZE = 1000  # 最大缓存1000条日志

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.__initialized = False
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if not self.__initialized:
            self.ui_handler = None
            self.log_cache = deque(maxlen=self.MAX_CACHE_SIZE)
            self.lock = Lock()
            self.__initialized = True
            
            # 初始化文件日志
            self.file_logger = logging.getLogger('FileLogger')
            self.file_logger.setLevel(logging.INFO)
            file_handler = logging.FileHandler('app.log')
            formatter = logging.Formatter('%(asctime)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.file_logger.addHandler(file_handler)

    def bind_ui(self, log_text_widget):
        """绑定UI组件（可延迟调用）"""
        with self.lock:
            self.ui_handler = log_text_widget
            # 回放缓存日志
            for msg in self.log_cache:
                self._write_to_ui(msg)

    def add_log(self, message: str):
        """添加日志（线程安全）"""
        with self.lock:
            # 记录到文件
            self.file_logger.info(message)
            
            # 缓存日志
            self.log_cache.append(message)
            
            # 如果UI已绑定，实时显示
            if self.ui_handler:
                self._write_to_ui(message)

    def _write_to_ui(self, message):
        """写入UI组件（内部方法）"""
        try:
            self.ui_handler.config(state='normal')
            self.ui_handler.insert(tk.END, f"{self._timestamp()} - {message}\n")
            self.ui_handler.config(state='disabled')
            self.ui_handler.see(tk.END)
        except Exception as e:
            print(f"UI日志写入失败: {str(e)}")

    def _timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")