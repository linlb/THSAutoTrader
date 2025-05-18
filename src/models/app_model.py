import json
import os
from ..common.operation_result import OperationResult  # 从common目录导入

class AppModel:
    def __init__(self):
        self._config = self._load_config()

    def get_target_app(self):
        return self._config.get('default_app_path')

    def set_target_app(self, path):
        self._config['default_app_path'] = path
        self._save_config()
        
    def get_trading_app(self):
        """获取下单程序路径，路径规则为：app_path同级目录下的xiadan.exe"""
        app_path = self.get_target_app()
        if app_path:
            return os.path.join(os.path.dirname(app_path), 'xiadan.exe')
        return None

    def _load_config(self):
        try:
            with open('config/app_config.json') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'default_app_path': 'D:\\同花顺软件\\同花顺\\hexin.exe'}

    def _save_config(self):
        # 确保config目录存在
        os.makedirs('config', exist_ok=True)
        with open('config/app_config.json', 'w') as f:
            json.dump(self._config, f) 