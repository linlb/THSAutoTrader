import json
from dataclasses import dataclass
import os

@dataclass
class OperationResult:
    success: bool
    error: str = None
    data: object = None

class ApplicationModel:
    def __init__(self):
        self._config = self._load_config()

    def get_target_app(self):
        return self._config.get('default_app_path')

    def set_target_app(self, path):
        self._config['default_app_path'] = path
        self._save_config()
        return OperationResult(True)

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