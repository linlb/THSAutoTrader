import tkinter as tk
import asyncio
import threading
from src.view.automation_view import AutomationView
from src.view.system_tray import SystemTray
from src.controller.automation_controller import AutomationController
from src.service.flask_service import FlaskApp
from src.service.signaling_server import WebRTCSignalingService
from src.service.window_monitor import WindowMonitor
from src.util.logger import Logger

class AutomationApp:
    def __init__(self, root):
        self.root = root
        self.logger = Logger()
        self.controller = AutomationController()
        
        # 初始化系统托盘
        self.system_tray = SystemTray(self.root, self)
        # 程序启动时就显示托盘图标
        self.system_tray.start_tray()

        # 初始化app视图
        self.view = self._init_view()
        
        # 初始化http服务
        self.flask_server = self.init_http_server()
        
        # 初始化WebRTC信令服务
        self.signaling_service = self.init_signaling_server()

        # 初始化窗口监控服务
        self.window_monitor = self.init_window_monitor()

        # 设置窗口关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)

    def _init_view(self):
        """初始化app视图"""
        view = AutomationView(self.root, controller=self.controller)
        view.pack(fill=tk.BOTH, expand=True)
        
        # 将应用实例引用传递给窗口，以便访问托盘功能
        self.root.app_instance = self
        
        return view

    def on_window_close(self):
        """处理窗口关闭事件 - 最小化到托盘而不是退出"""
        try:
            self.system_tray.hide_to_tray()
        except Exception as e:
            self.logger.add_log(f"最小化到托盘失败: {str(e)}")
            # 如果托盘失败，则正常退出
            self.quit_application()

    def quit_application(self):
        """真正退出应用程序"""
        try:
            self.logger.add_log("正在退出应用程序...")

            # 停止窗口监控
            if self.window_monitor:
                self.window_monitor.stop()

            # 停止托盘
            if self.system_tray:
                self.system_tray.stop_tray()

            # 退出主循环
            self.root.quit()
            self.root.destroy()

        except Exception as e:
            self.logger.add_log(f"退出程序失败: {str(e)}")

    def start(self):
        """启动应用程序"""
        self.root.title("下单辅助程序")
        self.root.geometry("500x300")
        # 设置窗口icon
        try:
            # 修改路径，假设icon.ico放在static目录下
            icon = tk.PhotoImage(file="static/icon.ico")
            self.root.iconphoto(True, icon)
        except Exception as e:
            print(f"无法加载icon: {e}")
        self.root.mainloop()

    def init_http_server(self):
        """初始化HTTP服务"""
        flask_server = FlaskApp(host='0.0.0.0', port=5000, controller=self.controller)
        flask_server.run_async()
        self.log(f"HTTP服务已启动")
        self.log(f"本地访问地址：http://localhost:{flask_server.port}/health")
        self.log(f"局域网访问地址：http://<本机IP地址>:{flask_server.port}/health")
        self.log(f"下单接口：http://<本机IP地址>:{flask_server.port}/xiadan?code=600000&status=1&price=12.34")
        self.log(f"获取持仓接口：http://<本机IP地址>:{flask_server.port}/position")
        return flask_server

    def init_signaling_server(self):
        """初始化WebRTC信令服务"""
        signaling_service = WebRTCSignalingService(host="0.0.0.0", port=8000)
        
        # 在后台线程中启动信令服务器
        def start_signaling_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(signaling_service.start_server())
                # 保持事件循环运行
                loop.run_forever()
            except Exception as e:
                self.log(f"信令服务器启动失败: {e}")
            finally:
                loop.close()
        
        # 启动信令服务器线程
        signaling_thread = threading.Thread(
            target=start_signaling_server,
            daemon=True,
            name="WebRTC-Signaling-Server"
        )
        signaling_thread.start()
        
        self.log(f"WebRTC信令服务已启动在端口 8000")
        self.log(f"WebSocket端点: ws://0.0.0.0:8000")

        return signaling_service

    def init_window_monitor(self):
        """初始化窗口监控服务"""
        monitor_config = self.controller.model.get_window_monitor_config()
        check_interval = monitor_config.get('check_interval', 1.5)

        window_monitor = WindowMonitor(check_interval=check_interval)

        # 如果配置启用了监控，则自动启动
        if monitor_config.get('enabled', True):
            target_app = self.controller.model.get_target_app()
            if target_app:
                window_monitor.start(target_app)
                self.log(f"窗口监控已启动，监控目标: {target_app}")
            else:
                self.log("窗口监控未启动：未配置目标程序路径")
        else:
            self.log("窗口监控已禁用（可在配置文件中启用）")

        return window_monitor

    def log(self, message):
        """使用新的Logger类记录日志"""
        self.logger.add_log(message)

        
