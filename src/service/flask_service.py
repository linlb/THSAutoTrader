from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
from src.util.logger import Logger
import time
from src.service.window_service import WindowService
from src.service.proxy_service import ProxyService
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

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
        # 基础健康检查
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "success", "timestamp": time.time()})
        
        # 获取资金余额
        @self.app.route('/balance', methods=['GET'])
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
        @self.app.route('/today_orders', methods=['GET'])
        def get_today_orders():
            try:
                orders = self.controller.get_today_orders()
                return jsonify({
                    "status": "success",
                    "data": orders
                })
            except Exception as e:
                self.logger.add_log(f"获取当日委托失败: {str(e)}")
                return jsonify({
                    "status": "error",
                    "message": f"获取当日委托失败: {str(e)}"
                }), 500

        @self.app.route('/current_page', methods=['GET'])
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
        def click():
            try:
                self.controller.handle_click()
                return jsonify({"status": "success", "message": "下单成功"})
            except Exception as e:
                self.logger.add_log(f"下单异常: {str(e)}")
                return jsonify({"status": "error", "message": f"下单异常: {str(e)}"}), 500
        
        # send_key
        @self.app.route('/send_key', methods=['GET'])
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
        
        # 下单点击
        @self.app.route('/xiadan', methods=['GET'])
        def xiadan():
            # 从url上获取参数，code
            code = request.args.get('code')
            status = request.args.get('status')
            amount = request.args.get('amount')
            position = request.args.get('position')
            price = request.args.get('price')

            requested_price = None
            amount_int = None
            position_int = None
            if price is not None:
                requested_price = price.strip()
                if requested_price == '':
                    user_message = "你传了价格参数，但价格是空的。请填一个大于0的价格，例如 12.34。"
                    return jsonify({
                        "status": "error",
                        "message": user_message,
                        "user_message": user_message,
                        "error_reason": user_message
                    }), 400
                try:
                    price_decimal = Decimal(requested_price)
                except InvalidOperation:
                    user_message = f"价格“{requested_price}”看起来不是数字。请改成数字格式，例如 12.34。"
                    return jsonify({
                        "status": "error",
                        "message": user_message,
                        "user_message": user_message,
                        "error_reason": user_message
                    }), 400

                if not price_decimal.is_finite():
                    user_message = "价格格式不对，请输入正常数字，例如 12.34。"
                    return jsonify({
                        "status": "error",
                        "message": user_message,
                        "user_message": user_message,
                        "error_reason": user_message
                    }), 400

                if price_decimal <= 0:
                    user_message = "价格必须大于0。请填写一个正常的价格，例如 12.34。"
                    return jsonify({
                        "status": "error",
                        "message": user_message,
                        "user_message": user_message,
                        "error_reason": user_message
                    }), 400

                if price_decimal.as_tuple().exponent < -2:
                    user_message = "价格最多支持2位小数，请修改后再下单。"
                    return jsonify({
                        "status": "error",
                        "message": user_message,
                        "user_message": user_message,
                        "error_reason": user_message
                    }), 400

                normalized_price = str(price_decimal.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP))
                if '.' in normalized_price:
                    decimal_length = len(normalized_price.split('.', 1)[1].rstrip('0'))
                    if decimal_length > 3:
                        user_message = "价格小数位太多了，最多支持3位小数。请修改后再下单。"
                        return jsonify({
                            "status": "error",
                            "message": user_message,
                            "user_message": user_message,
                            "error_reason": user_message
                        }), 400

                requested_price = normalized_price
            try:
                if code is None:
                    return jsonify({"status": "error", "message": "code不能为空"})
                if status is None:
                    return jsonify({"status": "error", "message": "status不能为空,1:闪电买入,2:闪电卖出"})
                if status not in ['1', '2']:
                    user_message = "status参数不对，只能填1或2。1是买入，2是卖出。"
                    return jsonify({
                        "status": "error",
                        "message": user_message,
                        "user_message": user_message,
                        "error_reason": user_message
                    }), 400

                # amount参数校验（传了就按amount）
                if amount is not None and str(amount).strip() != '':
                    try:
                        amount_int = int(str(amount).strip())
                    except ValueError:
                        user_message = "amount参数必须是整数股数。"
                        return jsonify({
                            "status": "error",
                            "message": user_message,
                            "user_message": user_message,
                            "error_reason": user_message
                        }), 400
                    if amount_int <= 0:
                        user_message = "amount必须大于0。"
                        return jsonify({
                            "status": "error",
                            "message": user_message,
                            "user_message": user_message,
                            "error_reason": user_message
                        }), 400

                # amount未传时，必须传position
                if amount_int is None:
                    if position is None or str(position).strip() == '':
                        user_message = "未传amount时必须传position(1/2/3/4)。"
                        return jsonify({
                            "status": "error",
                            "message": user_message,
                            "user_message": user_message,
                            "error_reason": user_message
                        }), 400
                    try:
                        position_int = int(str(position).strip())
                    except ValueError:
                        user_message = "position参数必须为数字，且只能是1/2/3/4。"
                        return jsonify({
                            "status": "error",
                            "message": user_message,
                            "user_message": user_message,
                            "error_reason": user_message
                        }), 400
                    if position_int not in [1, 2, 3, 4]:
                        user_message = "position参数错误，可选值为1,2,3,4。"
                        return jsonify({
                            "status": "error",
                            "message": user_message,
                            "user_message": user_message,
                            "error_reason": user_message
                        }), 400

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
                # 获取window（按关键控件匹配，避免取错第一个 #32770 对话框）
                window = self.window_service.get_best_match_window(
                    {'class_name': '#32770', 'title': ''},
                    [1006, 0x1006, 1033, 0x1033, 1034, 0x1034],
                    min_match_count=2
                )
                if window is None:
                    user_message = "没有找到闪电下单窗口，请确认同花顺交易窗口已经打开。"
                    return jsonify({
                        "status": "error",
                        "message": user_message,
                        "user_message": user_message,
                        "error_reason": user_message
                    }), 500

                # 如果有price参数，先输入价格（兼容十进制/十六进制控件ID）
                if requested_price is not None:
                    try:
                        self.window_service.input_text_to_element(
                            window,
                            [1033, 0x1033],
                            requested_price,
                            clear_existing=True
                        )
                    except Exception as price_err:
                        self.logger.add_log(f"价格输入失败: {str(price_err)}")
                        user_message = "价格输入失败，已中止下单。请检查价格输入框是否可编辑，然后重试。"
                        return jsonify({
                            "status": "error",
                            "message": user_message,
                            "user_message": user_message,
                            "error_reason": user_message,
                            "requested_price": requested_price,
                            "price_applied": False
                        }), 500

                available_amount = None
                order_amount = amount_int
                amount_source = "amount"

                # amount未传时，按position计算下单数量
                if order_amount is None:
                    self.logger.add_log("amount未传，按position计算下单数量")

                    # 点击刷新按钮更新可用数量
                    self.window_service.click_element(window, 1528)
                    time.sleep(0.1)

                    # 获取可用数量(AutomationId: 1034)
                    available_element = self.window_service.find_element_in_window(window, 1034)
                    if available_element is None:
                        return jsonify({
                            "status": "error",
                            "message": "未找到可用数量元素",
                            "user_message": "未找到可用数量元素",
                            "error_reason": "未找到可用数量元素"
                        }), 500

                    available_amount_str = available_element.window_text().strip()
                    if available_amount_str == '' or available_amount_str == '0':
                        return jsonify({
                            "status": "error",
                            "message": "可用数量为0，无法下单",
                            "user_message": "可用数量为0，无法下单",
                            "error_reason": "可用数量为0，无法下单"
                        }), 400

                    try:
                        available_amount = int(available_amount_str)
                    except ValueError:
                        return jsonify({
                            "status": "error",
                            "message": f"可用数量格式错误: {available_amount_str}",
                            "user_message": f"可用数量格式错误: {available_amount_str}",
                            "error_reason": f"可用数量格式错误: {available_amount_str}"
                        }), 500

                    order_amount = (available_amount // position_int // 100) * 100
                    if order_amount < 100:
                        return jsonify({
                            "status": "error",
                            "message": f"按position计算后的下单数量({order_amount}股)小于100股，无法下单",
                            "user_message": f"按position计算后的下单数量({order_amount}股)小于100股，无法下单",
                            "error_reason": f"按position计算后的下单数量({order_amount}股)小于100股，无法下单"
                        }), 400
                    amount_source = "position"

                # 输入下单数量
                self.window_service.input_text_to_element(
                    window,
                    [1034, 0x1034],
                    str(order_amount),
                    clear_existing=True
                )
                
                # 下单点击
                self.window_service.click_element(window, [1006, 0x1006])
                action_text = "买入" if status == '1' else "卖出"
                return jsonify({
                    "status": "success",
                    "message": f"已发送按键 {keyStr}",
                    "user_message": f"{action_text}下单请求已发送，请调用/confirm_order完成确认",
                    "requested_price": requested_price,
                    "price_applied": requested_price is not None,
                    "data": {
                        "order_amount": order_amount,
                        "amount_source": amount_source,
                        "position": position_int,
                        "available_amount": available_amount
                    }
                })
            except Exception as e:
                self.logger.add_log(f"按键发送失败: {str(e)}")
                user_message = "下单失败了。请确认交易窗口在前台且可操作，然后再试一次。"
                return jsonify({
                    "status": "error",
                    "message": user_message,
                    "user_message": user_message,
                    "error_reason": user_message
                }), 500
               
        # 撤单接口
        @self.app.route('/cancel_all_orders', methods=['GET'])
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
        def confirm_order():
            try:
                # 只做“确认下单”动作，不再处理数量与仓位
                window = self.window_service.get_best_match_window(
                    {'class_name': '#32770', 'title': ''},
                    [1006, 0x1006],
                    min_match_count=1
                )
                if window is None:
                    return jsonify({"status": "error", "message": "未找到下单确认弹窗"}), 500

                self.logger.add_log(f"点击确认买入按钮")
                self.window_service.click_element(window, [1006, 0x1006])

                return jsonify({
                    "status": "success",
                    "message": "下单确认成功"
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
