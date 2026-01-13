"""GitHub 项目信息获取插件"""

# 导入 handlers 以注册沙盒方法
from . import handlers  # noqa: F401
from .plugin import plugin

__all__ = ["plugin"]
