import tkinter as tk
from tkinter import ttk
from tkinterweb import HtmlFrame
from src.util.logger import Logger
import threading

class AutomationView(ttk.Frame):
    def __init__(self, master, controller = None):
        super().__init__(master)
        # 先初始化控制器和服务
        self.controller = controller
        self._init_components()
        self._bind_logger()
        
        # 创建控制面板容器
        self.control_panel = ttk.Frame(self, width=300, padding=10)
        self.control_panel.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
        
        # 主容器使用pack布局
        main_container = ttk.Frame(self)
        main_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 创建主界面组件
        self.create_widgets(main_container)
        
        # 新增WebView组件
        # self._create_webview(main_container)
        
        # 将原控制按钮移动到控制面板
        self._create_control_buttons()
        
        self.pack(fill=tk.BOTH, expand=True)

    def _init_components(self):
        """初始化界面组件"""
        # 日志组件初始化
        log_container = ttk.Frame(self)
        log_container.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        self.log_text = tk.Text(log_container, height=8, state='disabled')
        scrollbar = ttk.Scrollbar(log_container, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _bind_logger(self):
        """绑定日志UI组件"""
        Logger().bind_ui(self.log_text)

    def create_widgets(self, parent_frame):
        """在主容器中创建控件"""
        app_frame = ttk.Frame(parent_frame)
        app_frame.pack(pady=5, fill=tk.X, padx=10)
        
        ttk.Label(app_frame, text="应用路径:").grid(row=0, column=0, sticky='w')
        self.app_entry = ttk.Entry(app_frame, width=30)
        self.app_entry.grid(row=0, column=1, padx=5, sticky='ew')
        self.app_entry.insert(0, self.controller.model.get_target_app())
        self.app_entry.bind("<FocusOut>", self.select_application)
        
        # 在应用路径行添加透明度控制
        ttk.Label(app_frame, text="透明度:").grid(row=0, column=3, padx=(10,0))
        self.alpha_scale = ttk.Scale(app_frame, from_=0.5, to=1.0, 
                                   command=self.update_alpha)
        self.alpha_scale.set(0.9)  # 现在这个操作会触发日志记录
        self.alpha_scale.grid(row=0, column=4, padx=5)
        
        # 新增按键指令输入行
        key_frame = ttk.Frame(parent_frame)
        key_frame.pack(pady=5, fill=tk.X, padx=10)
        
        ttk.Label(key_frame, text="按键指令:").grid(row=0, column=0, sticky='w')
        self.key_entry = ttk.Entry(key_frame, width=30)
        self.key_entry.grid(row=0, column=1, padx=5)
        
        ttk.Button(key_frame, text="发送按键", 
                  command=lambda: self.controller.handle_send_key(self.key_entry.get().strip())).grid(row=0, column=2)
        # 新增鼠标指令输入行
        mouse_frame = ttk.Frame(parent_frame)
        mouse_frame.pack(pady=5, fill=tk.X, padx=10)
        
        ttk.Label(mouse_frame, text="鼠标指令:").grid(row=0, column=0, sticky='w')
        # self.mouse_entry = ttk.Entry(mouse_frame, width=30)
        # self.mouse_entry.grid(row=0, column=1, padx=5)
        
        # ttk.Button(mouse_frame, text="下单点击", 
        #           command=self.controller.handle_click).grid(row=0, column=2)
        
        ttk.Button(mouse_frame, text="获取持仓", 
                  command=self.controller.get_position).grid(row=0, column=3)
        
        # 新增获取资金余额按钮
        ttk.Button(mouse_frame, text="获取资金", 
                  command=self.controller.get_balance).grid(row=0, column=4)
        
        # 添加撤单功能框架
        cancel_frame = ttk.Frame(parent_frame)
        cancel_frame.pack(pady=5, fill=tk.X, padx=10)
        
        ttk.Label(cancel_frame, text="撤单操作:").grid(row=0, column=0, sticky='w')
          
        # 批量撤单按钮
        ttk.Button(cancel_frame, text="撤销所有", 
                  command=self.controller.handle_cancel_all_orders).grid(row=0, column=3, padx=5)
        
    def select_application(self, event=None):
        """通过输入路径选择应用程序"""
        self.controller.model.set_target_app(self.app_entry.get().strip())
        Logger().add_log(f"已设置目标应用路径: {self.controller.model.get_target_app()}")

    def update_alpha(self, value):
        """更新窗口透明度"""
        self.master.attributes('-alpha', float(value))
        Logger().add_log(f"窗口透明度已更新为: {value}")

    def update_log(self, message):
        """更新日志显示"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)

    def _create_control_buttons(self):
        """在控制面板创建通用控制按钮"""
        def activate_and_save():
            # 先保存应用路径
            self.select_application()
            # 再激活窗口
            self.controller.handle_activate_window()
            
        ttk.Button(
            self.control_panel,
            text="激活窗口",
            command=activate_and_save
        ).pack(pady=5)

    def get_key_command(self):
        """获取按键指令输入"""
        return self.key_entry.get().strip()
    
    def _handle_cancel_order(self):
        """处理撤单操作"""
        order_id = self.order_id_entry.get().strip()
        if order_id:
            self.controller.handle_cancel_order(order_id)
        else:
            self.controller.handle_cancel_order()

    def _create_webview(self, parent_frame):
        """创建WebView组件"""
        web_frame = ttk.Frame(parent_frame)
        web_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建HtmlFrame
        self.webview = HtmlFrame(web_frame, messages_enabled=False)
        self.webview.pack(fill=tk.BOTH, expand=True)
        
        # 增加加载状态检测
        self._load_webpage_with_retry("https://www.bing.com", retries=3)

    def _load_webpage_with_retry(self, url, retries=3):
        """带重试机制的页面加载"""
        try:
            self.webview.load_url(url)
            Logger().add_log(f"成功加载页面: {url}")
        except Exception as e:
            if retries > 0:
                Logger().add_log(f"页面加载失败，正在重试... ({retries}次剩余)")
                threading.Timer(2.0, lambda: self._load_webpage_with_retry(url, retries-1)).start()
            else:
                Logger().add_log(f"无法加载页面: {url}，错误: {str(e)}")
