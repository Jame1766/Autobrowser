"""
配置管理模块
"""
import os
import yaml
from pathlib import Path

class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """加载配置文件"""
        # 从项目根目录查找配置文件
        possible_paths = [
            Path(__file__).parent.parent.parent / "config" / "settings.yaml",
            Path.cwd() / "config" / "settings.yaml",
        ]
        config_path = None
        for path in possible_paths:
            if path.exists():
                config_path = path
                break

        if not config_path:
            raise FileNotFoundError("找不到配置文件 settings.yaml")

        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

    def get(self, key, default=None):
        """获取配置项"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    @property
    def crawler(self):
        return self._config.get('crawler', {})

    @property
    def publisher(self):
        return self._config.get('publisher', {})

    @property
    def xiaohongshu(self):
        return self._config.get('xiaohongshu', {})

# 全局配置实例
config = Config()
