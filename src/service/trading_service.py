import time
from pywinauto import Desktop
from pywinauto.keyboard import send_keys

from src.models.app_model import AppModel
from src.service.today_orders_service import TodayOrdersService
from src.service.window_service import WindowService
from src.util.logger import Logger


class TradingService:
    def __init__(self):
        self.window_service = WindowService()
        self.today_orders_service = TodayOrdersService()
        self.model = AppModel()
        self.logger = Logger()

    def _get_today_orders_safe(self):
        try:
            data = self.today_orders_service.get_today_orders()
            if isinstance(data, list):
                return data
            return []
        except Exception as e:
            self.logger.add_log(f"获取当日委托失败(用于撤单校验): {str(e)}")
            return []

    def _pick_field(self, row, candidates):
        if not isinstance(row, dict):
            return ""

        normalized = {}
        for key, value in row.items():
            normalized[str(key).strip()] = value

        for candidate in candidates:
            for key, value in normalized.items():
                if candidate == key or candidate in key:
                    return str(value or "").strip()
        return ""

    def _to_number(self, value):
        if value is None:
            return None
        text = str(value).strip().replace(",", "")
        if text == "":
            return None
        try:
            return float(text)
        except Exception:
            return None

    def _is_buy_order(self, row):
        operation = self._pick_field(row, ["操作", "买卖", "业务", "鎿嶄綔", "涔板崠", "涓氬姟"])
        return ("买" in operation) or ("涔" in operation)

    def _is_sell_order(self, row):
        operation = self._pick_field(row, ["操作", "买卖", "业务", "鎿嶄綔", "涔板崠", "涓氬姟"])
        return ("卖" in operation) or ("鍗" in operation)

    def _is_cancellable(self, row):
        # 1) 优先按状态文本判断
        remark = self._pick_field(row, ["备注", "状态"])
        status = self._pick_field(row, ["委托状态", "状态", "说明"])
        text = f"{remark} {status}".strip()

        terminal_flags = [
            "已撤", "撤单", "废单", "全成", "已成", "已拒", "无效",
            "宸叉挙", "鎾ゅ崟", "搴熷崟", "鍏ㄦ垚", "宸叉垚",
        ]
        if any(flag in text for flag in terminal_flags):
            return False

        active_flags = ["未成", "已报", "待撤", "部成", "部分成交"]
        if any(flag in text for flag in active_flags):
            return True

        # 2) 状态字段不稳定时，按“委托数量 > 成交数量”判断是否未成交完
        entrust_qty = self._to_number(
            self._pick_field(row, ["委托数量", "申报数量", "数量"])
        )
        deal_qty = self._to_number(
            self._pick_field(row, ["成交数量", "已成数量"])
        )
        if entrust_qty is not None and deal_qty is not None:
            return entrust_qty > deal_qty

        return False

    def _count_cancellable_orders(self, orders, cancel_type):
        count = 0
        for row in orders:
            if not self._is_cancellable(row):
                continue
            if cancel_type == "X" and not self._is_buy_order(row):
                continue
            if cancel_type == "C" and not self._is_sell_order(row):
                continue
            count += 1
        return count

    def _is_cancelled_record(self, row):
        remark = self._pick_field(row, ["备注", "状态"])
        status = self._pick_field(row, ["委托状态", "状态", "说明"])
        text = f"{remark} {status}"
        cancelled_flags = ["已撤", "撤单", "废单"]
        return any(flag in text for flag in cancelled_flags)

    def get_pending_orders(self):
        """
        获取未撤销的当日委托数据。
        """
        orders = self._get_today_orders_safe()
        pending_orders = [row for row in orders if not self._is_cancelled_record(row)]
        self.logger.add_log(
            f"获取未撤销委托完成，总数:{len(orders)}，未撤销:{len(pending_orders)}"
        )
        return pending_orders

    def _confirm_cancel_dialogs(self, max_rounds=8):
        clicked_any = False
        for _ in range(max_rounds):
            clicked_this_round = False
            dialogs = Desktop(backend="uia").windows(class_name="#32770")
            for dialog in dialogs:
                title = str(dialog.window_text() or "")
                if "交易系统5.0" in title or "浜ゆ槗绯荤粺5.0" in title:
                    continue

                for control_id in (1, 1006):
                    try:
                        button = dialog.child_window(control_id=control_id)
                        if button.exists():
                            button.click_input()
                            clicked_any = True
                            clicked_this_round = True
                            time.sleep(0.1)
                            break
                    except Exception:
                        continue

                if not clicked_this_round:
                    try:
                        dialog.set_focus()
                        send_keys("{ENTER}")
                        clicked_any = True
                        clicked_this_round = True
                        time.sleep(0.1)
                    except Exception:
                        continue

            if not clicked_this_round:
                break
            time.sleep(0.15)
        return clicked_any

    def cancel_all_orders(self, cancel_type=None):
        """
        撤销委托
        Args:
            cancel_type (str, optional):
                - 'A' 或 None: 全部撤单 (control_id: 30001)
                - 'X': 撤买 (control_id: 30002)
                - 'C': 撤卖 (control_id: 30003)
        """
        try:
            if cancel_type not in (None, "A", "X", "C"):
                raise Exception(f"不支持的撤单类型: {cancel_type}")

            normalized_type = "A" if cancel_type in (None, "A") else cancel_type

            # 先从“当日委托”判断是否存在未成交单，再决定是否进入 F3 执行撤单
            before_orders = self._get_today_orders_safe()
            before_count = self._count_cancellable_orders(before_orders, normalized_type)
            if before_count <= 0:
                self.logger.add_log(f"{normalized_type}撤单前无未成交/可撤委托，跳过F3撤单流程")
                return True

            trading_path = self.model.get_trading_app()
            self.window_service.activate_window(trading_path)

            window = self.window_service.get_target_window({"title": "网上股票交易系统5.0"})
            window.click_input()
            time.sleep(0.1)

            # 刷新后进入 F3 撤单页
            self.window_service.send_key("F5")
            time.sleep(0.1)
            self.window_service.send_key("F3")
            self.logger.add_log(f"检测到可撤单 {before_count} 条，已进入F3撤单页面")
            time.sleep(0.2)

            control_id_map = {
                "A": 30001,  # 全部撤单
                "X": 30002,  # 撤买
                "C": 30003,  # 撤卖
            }
            control_id = control_id_map.get(normalized_type, 30001)

            self.window_service.click_element(window, control_id)
            time.sleep(0.2)
            self._confirm_cancel_dialogs()

            time.sleep(0.4)
            self.window_service.send_key("F5")
            time.sleep(0.2)

            after_orders = self._get_today_orders_safe()
            remaining_count = self._count_cancellable_orders(after_orders, normalized_type)

            operation_name = {
                30001: "全部撤单",
                30002: "撤买",
                30003: "撤卖",
            }.get(control_id, "撤单")

            if remaining_count == 0:
                self.logger.add_log(
                    f"{operation_name}完成，撤单前可撤:{before_count}，撤单后可撤:{remaining_count}"
                )
                return True

            self.logger.add_log(
                f"{operation_name}疑似未完全生效，撤单前可撤:{before_count}，撤单后可撤:{remaining_count}"
            )
            return False

        except Exception as e:
            error_msg = f"撤单操作失败: {str(e)}"
            self.logger.add_log(error_msg)
            raise Exception(error_msg)
