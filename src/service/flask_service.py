from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import functools
from src.util.logger import Logger
import time
import pyautogui
from src.service.window_service import WindowService
from src.service.proxy_service import ProxyService

class FlaskApp:
    def __init__(self, host='0.0.0.0', port=5000, controller=None):
        """
        初始化Flask应用
        Args:
            host (str): 监听地址，默认localhost
            port (int): 监听端口，默认5000
        """
        self.host = host
        self.port = port
        self.controller = controller
        self.window_service = WindowService()
        self.app = Flask(__name__)
        self.running = False
        self.thread = None
        self.logger = Logger.get_instance()

        # 全局GUI操作锁: THS窗口是唯一共享资源(焦点/当前页面),
        # 所有操作窗口的接口必须串行执行,否则并发请求会互相抢焦点、读到错位数据。
        # 注意: 本次只覆盖HTTP接口,Tkinter界面和window_monitor后台线程暂未纳入同一把锁。
        self.gui_lock = threading.Lock()
        # 抢锁超时(秒): 需大于单次GUI操作的最长耗时(如OCR/下单),抢不到返回繁忙避免请求堆积
        self.gui_lock_timeout = 30

        # 初始化代理服务 - 支持高并发
        self.proxy_service = ProxyService(
            cache_ttl=10,           # 缓存10秒
            pool_connections=100,   # 连接池数量(翻倍)
            pool_maxsize=200,       # 最大并发连接数(翻倍)
            max_retries=3           # 失败自动重试3次
        )

        # 配置CORS
        CORS(self.app)

        # 设置JSON编码
        self.app.config['JSON_AS_ASCII'] = False

        self._register_routes()

    def add_route(self, path, handler, methods=['GET']):
        """
        添加路由
        Args:
            path (str): 请求路径
            handler (callable): 处理函数
            methods (list): 支持的HTTP方法
        """
        def wrapper():
            # 处理请求数据
            data = None
            if request.method in ['POST', 'PUT']:
                if request.is_json:
                    data = request.get_json()
                else:
                    data = request.data
            
            # 调用处理函数并返回响应
            result = handler(data)
            return jsonify(result)
        
        # 注册路由
        self.app.add_url_rule(
            path,
            endpoint=path,
            view_func=wrapper,
            methods=methods
        )

    def run(self):
        """启动Flask服务器"""
        if not self.running:
            self._run_server()
            self.running = True

    def run_async(self):
        """异步启动服务器"""
        if not self.running:
            self.thread = threading.Thread(target=self.run)
            self.thread.daemon = True
            self.thread.start()
            self.running = True

    def stop(self):
        """停止服务器（需要自行实现关闭逻辑）"""
        # Flask开发服务器没有原生停止方法，通常通过发送中断信号
        self.running = False
        print("请使用Ctrl+C停止服务器")

    def _run_server(self):
        try:
            # 添加更详细的启动日志
            self.logger.add_log(f"HTTP服务初始化完成，监听地址：{self.host}:{self.port}")
            self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)
        except Exception as e:
            self.logger.add_log(f"HTTP服务启动失败: {str(e)}")
            raise  # 抛出异常以便上层捕获
    def _register_routes(self):
        # GUI操作互斥装饰器: 串行化所有操作THS窗口的接口
        def with_gui_lock(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                acquired = self.gui_lock.acquire(timeout=self.gui_lock_timeout)
                if not acquired:
                    self.logger.add_log(f"GUI操作繁忙,接口 {func.__name__} 抢锁超时({self.gui_lock_timeout}s)")
                    return jsonify({
                        "status": "busy",
                        "message": "系统繁忙,GUI操作正被占用,请稍后重试"
                    }), 429
                try:
                    return func(*args, **kwargs)
                finally:
                    self.gui_lock.release()
            return wrapper

        # 基础健康检查
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "success", "timestamp": time.time()})
        
        # 获取资金余额
        @self.app.route('/balance', methods=['GET'])
        @with_gui_lock
        def get_balance():
            try:
                # 调用controller获取资金余额
                balance = self.controller.get_balance()
                return jsonify({
                    "status": "success",
                    "data": balance
                })
            except Exception as e:
                self.logger.add_log(f"获取资金余额失败: {str(e)}")
                return jsonify({
                    "status": "error",
                    "message": f"获取资金余额失败: {str(e)}"
                }), 500
        
        # 获取持仓信息
        @self.app.route('/position', methods=['GET'])
        @with_gui_lock
        def get_position():
            try:
                # 调用controller获取持仓信息
                position = self.controller.get_position()
                return jsonify({
                    "status": "success",
                    "data": position
                })
            except Exception as e:
                self.logger.add_log(f"获取持仓失败: {str(e)}")
                return jsonify({
                    "status": "error",
                    "message": f"获取持仓失败: {str(e)}"
                }), 500

        # 获取今日成交
        @self.app.route('/today_trades', methods=['GET'])
        @with_gui_lock
        def get_today_trades():
            try:
                # 调用controller获取今日成交信息
                trades = self.controller.get_today_trades()
                return jsonify({
                    "status": "success",
                    "data": trades
                })
            except Exception as e:
                self.logger.add_log(f"获取今日成交失败: {str(e)}")
                return jsonify({
                    "status": "error",
                    "message": f"获取今日成交失败: {str(e)}"
                }), 500

        # 获取当前页面
        @self.app.route('/current_page', methods=['GET'])
        @with_gui_lock
        def get_current_page():
            try:
                # 调用controller获取当前页面信息
                page_info = self.controller.get_current_page()
                return jsonify({
                    "status": "success",
                    "data": page_info
                })
            except Exception as e:
                self.logger.add_log(f"获取当前页面失败: {str(e)}")
                return jsonify({
                    "status": "error",
                    "message": f"获取当前页面失败: {str(e)}"
                }), 500

        # 鼠标点击
        @self.app.route('/click', methods=['GET'])
        @with_gui_lock
        def click():
            """鼠标点击接口
            参数:
                x (int): 点击的x坐标
                y (int): 点击的y坐标
            示例:
                /click?x=100&y=200  # 点击坐标(100, 200)
            """
            try:
                x = request.args.get('x')
                y = request.args.get('y')

                # 参数校验
                if x is None or y is None:
                    return jsonify({"status": "error", "message": "x和y参数不能为空"}), 400

                try:
                    x_int = int(x)
                    y_int = int(y)
                except ValueError:
                    return jsonify({"status": "error", "message": "x和y参数必须为整数"}), 400

                # 先激活窗口
                self.controller.handle_activate_window()
                time.sleep(0.1)
                # 移动鼠标到指定坐标并点击
                pyautogui.click(x_int, y_int)
                self.logger.add_log(f"坐标点击: ({x_int}, {y_int})")
                return jsonify({
                    "status": "success",
                    "message": f"坐标点击成功: ({x_int}, {y_int})"
                })
            except Exception as e:
                self.logger.add_log(f"点击异常: {str(e)}")
                return jsonify({"status": "error", "message": f"点击异常: {str(e)}"}), 500
        
        # send_key
        @self.app.route('/send_key', methods=['GET'])
        @with_gui_lock
        def send_key():
            # 从url上获取参数，key
            key = request.args.get('key')
            try:
                # 先激活窗口
                self.controller.handle_activate_window()
                time.sleep(0.1)
                self.window_service.send_key(key)
                time.sleep(0.1)
                return jsonify({"status": "success", "message": f"已发送按键 {key}"})
            except Exception as e:
                self.logger.add_log(f"按键发送失败: {str(e)}")
                return jsonify({"status": "error", "message": f"按键发送失败: {str(e)}"})
        
        # 检测下单程序(xiadan.exe)进程是否在运行(纯进程探测,不操作GUI,无需加锁)
        @self.app.route('/check_trading_app', methods=['GET'])
        def check_trading_app():
            try:
                running = self.controller.handle_check_trading_app()
                return jsonify({"status": "success", "running": running})
            except Exception as e:
                self.logger.add_log(f"检测下单程序进程失败: {str(e)}")
                return jsonify({"status": "error", "message": f"检测下单程序进程失败: {str(e)}"}), 500

        # 下单点击
        @self.app.route('/xiadan', methods=['GET'])
        @with_gui_lock
        def xiadan():
            # 从url上获取参数，code
            code = request.args.get('code')
            status = request.args.get('status')
            amount = request.args.get('amount')
            try:
                if code is None:
                    return jsonify({"status": "error", "message": "code不能为空"})
                if status is None:
                    return jsonify({"status": "error", "message": "status不能为空,1:闪电买入,2:闪电卖出"})
                # 先激活窗口
                self.controller.handle_activate_window()
                time.sleep(0.1)
                # 发送代码
                keyStr = code + ' ENTER '
                if status == '1':
                    keyStr = keyStr + '21 ENTER'
                elif status == '2':
                    keyStr = keyStr + '23 ENTER'

                self.window_service.send_key(keyStr)
                # 获取window
                window = self.window_service.get_target_window({'class_name': '#32770', 'title':''})
                # 如果有amount参数
                if amount:
                    self.window_service.input_text_to_element(window, 1034, amount)
                
                # 下单点击
                self.window_service.click_element(window, 1006)
                return jsonify({"status": "success", "message": f"已发送按键 {keyStr}"})
            except Exception as e:
                self.logger.add_log(f"按键发送失败: {str(e)}")
                return jsonify({"status": "error", "message": f"下单异常: {str(e)}"})
               
        # 撤单接口
        @self.app.route('/cancel_all_orders', methods=['GET'])
        @with_gui_lock
        def cancel_all_orders():
            """撤单接口
            参数:
                type (str, optional): 撤单类型
                    - 'A' 或不传: 全部撤单 (control_id: 30001)
                    - 'X': 撤买 (control_id: 30002)
                    - 'C': 撤卖 (control_id: 30003)
            示例:
                /cancel_all_orders          # 全部撤单
                /cancel_all_orders?type=A   # 全部撤单
                /cancel_all_orders?type=X   # 撤买
                /cancel_all_orders?type=C   # 撤卖
            """
            # 获取撤单类型参数
            cancel_type = request.args.get('type')

            # 参数验证
            if cancel_type and cancel_type not in ['A', 'X', 'C']:
                return jsonify({
                    "status": "error",
                    "message": f"type参数错误,可选值为: A(全部撤单), X(撤买), C(撤卖)"
                }), 400

            try:
                result = self.controller.handle_cancel_all_orders(cancel_type)

                # 构造返回消息
                operation_name = {
                    'A': "全部撤单",
                    'X': "撤买",
                    'C': "撤卖",
                    None: "全部撤单"
                }.get(cancel_type, "撤单")

                if result:
                    return jsonify({
                        "status": "success",
                        "message": f"{operation_name}操作已执行",
                        "data": {"operation": operation_name, "type": cancel_type or 'A'}
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "message": f"{operation_name}失败"
                    })
            except Exception as e:
                self.logger.add_log(f"撤单失败: {str(e)}")
                return jsonify({"status": "error", "message": f"撤单失败: {str(e)}"})

        # 下单确认
        @self.app.route('/confirm_order', methods=['GET'])
        @with_gui_lock
        def confirm_order():
            # 从url上获取参数 position (可用仓位,可选)
            position = request.args.get('position')
            position_int = None

            try:
                # 参数校验(仅在传了position参数时)
                if position is not None:
                    try:
                        position_int = int(position)
                        if position_int not in [1, 2, 3, 4]:
                            return jsonify({"status": "error", "message": "position参数错误,可选值为1,2,3,4"}), 400
                    except ValueError:
                        return jsonify({"status": "error", "message": "position参数必须为数字"}), 400

                # 1. 选中下单确认弹窗
                window = self.window_service.get_target_window({'class_name': '#32770', 'title':''})
                if window is None:
                    return jsonify({"status": "error", "message": "未找到下单确认弹窗"}), 500

                # 1.5. 点击刷新按钮更新可用数量
                self.logger.add_log(f"点击刷新按钮更新可用数量")
                self.window_service.click_element(window, 1528)
                time.sleep(0.1)

                # 2. 获取可用数量(AutomationId: 1034)
                available_element = self.window_service.find_element_in_window(window, 1034)
                if available_element is None:
                    return jsonify({"status": "error", "message": "未找到可用数量元素"}), 500

                # 读取可用数量的值
                available_amount_str = available_element.window_text().strip()
                self.logger.add_log(f"获取到可用数量: {available_amount_str}")

                # 校验可用数量是否为0或空
                if available_amount_str == '0' or available_amount_str == '':
                    return jsonify({"status": "error", "message": f"可用数量为0,无法下单"}), 400

                # 将可用数量转换为数字
                try:
                    available_amount = int(available_amount_str)
                except ValueError:
                    return jsonify({"status": "error", "message": f"可用数量格式错误: {available_amount_str}"}), 500

                # 计算下单数量
                if position_int is not None:
                    # 根据仓位整除计算实际买入数量,向下取100的整
                    order_amount = (available_amount // position_int // 100) * 100
                    self.logger.add_log(f"可用数量: {available_amount}, 仓位: 1/{position_int}, 下单数量: {order_amount}")

                    # 校验下单数量是否小于100股
                    if order_amount < 100:
                        return jsonify({
                            "status": "error",
                            "message": f"计算后的下单数量({order_amount}股)小于100股,无法下单"
                        }), 400

                    # 3. 根据仓位参数点击对应的仓位选择按钮
                    # 1对应12092, 2对应12093, 3对应12094, 4对应12095
                    position_button_id = 12092 + position_int - 1
                    self.logger.add_log(f"点击仓位选择按钮,AutomationId: {position_button_id}")
                    self.window_service.click_element(window, position_button_id)
                    time.sleep(0.1)
                else:
                    # 满仓,下单数量等于可用数量
                    order_amount = available_amount
                    self.logger.add_log(f"满仓下单,可用数量: {available_amount}, 下单数量: {order_amount}")

                # 4. 点击确认买入按钮(AutomationId: 1006)
                self.logger.add_log(f"点击确认买入按钮")
                self.window_service.click_element(window, 1006)

                # 构造返回消息
                if position_int is not None:
                    message = f"下单确认成功,仓位:{position_int},可用数量:{available_amount},下单数量:{order_amount}"
                else:
                    message = f"下单确认成功,满仓,可用数量:{available_amount},下单数量:{order_amount}"

                return jsonify({
                    "status": "success",
                    "message": message,
                    "data": {
                        "available_amount": available_amount,
                        "position": position_int,
                        "order_amount": order_amount
                    }
                })
            except Exception as e:
                self.logger.add_log(f"下单确认失败: {str(e)}")
                return jsonify({"status": "error", "message": f"下单确认失败: {str(e)}"}), 500

        # 高性能代理接口
        @self.app.route('/proxy/<path:url>', methods=['GET', 'POST', 'PUT', 'DELETE'])
        def proxy(url):
            """
            高性能代理接口 - 委托给ProxyService处理

            前端调用: http://localhost:5000/proxy/basic.10jqka.com.cn/mapp/300033/stock_base_info.json
            实际转发: https://basic.10jqka.com.cn/mapp/300033/stock_base_info.json
            """
            return self.proxy_service.proxy_request(url, request)

        # 代理统计接口
        @self.app.route('/proxy/stats', methods=['GET'])
        def proxy_stats():
            """获取代理服务的统计信息"""
            try:
                stats = self.proxy_service.get_stats()
                return jsonify({
                    "status": "success",
                    "data": stats
                })
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500