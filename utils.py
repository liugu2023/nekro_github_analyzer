"""GitHub 插件工具函数模块 - 参数验证、异常处理、返回值格式化、缓存管理"""

from typing import Optional, Callable, Any, TypeVar, Generic
import functools
from datetime import datetime, timezone, timedelta
from collections import OrderedDict
from nekro_agent.core import logger

T = TypeVar("T")


class ValidationError(ValueError):
    """参数验证错误"""

    pass


class ParameterValidator:
    """参数验证工具类"""

    @staticmethod
    def validate_github_url(github_url: Any) -> str:
        """验证 GitHub URL 参数

        Args:
            github_url: GitHub URL 或 owner/repo 格式

        Returns:
            str: 有效的 github_url

        Raises:
            ValidationError: 如果参数无效
        """
        if not github_url or not isinstance(github_url, str):
            raise ValidationError("github_url 参数不能为空")
        return github_url

    @staticmethod
    def validate_per_page(per_page: int, default: int = 10) -> int:
        """验证分页参数

        Args:
            per_page: 每页数量
            default: 默认值

        Returns:
            int: 有效的 per_page (1-100)
        """
        if per_page < 1 or per_page > 100:
            return default
        return per_page

    @staticmethod
    def validate_page(page: int) -> int:
        """验证页码参数

        Args:
            page: 页码

        Returns:
            int: 有效的页码 (最小1)
        """
        return max(1, page)

    @staticmethod
    def validate_number(
        value: Any,
        name: str,
        min_value: int = 0,
        allow_zero: bool = False,
    ) -> int:
        """验证数值参数

        Args:
            value: 要验证的值
            name: 参数名称（用于错误消息）
            min_value: 最小值
            allow_zero: 是否允许0

        Returns:
            int: 有效的数值

        Raises:
            ValidationError: 如果参数无效
        """
        if not isinstance(value, int) or value < min_value:
            if allow_zero and value == 0:
                return 0
            raise ValidationError(f"{name} 必须是有效的正整数")
        return value

    @staticmethod
    def validate_string(value: Any, name: str) -> str:
        """验证字符串参数

        Args:
            value: 要验证的值
            name: 参数名称

        Returns:
            str: 有效的字符串

        Raises:
            ValidationError: 如果参数无效
        """
        if not value or not isinstance(value, str):
            raise ValidationError(f"{name} 参数不能为空")
        return value


class ResponseFormatter:
    """返回值格式化工具类"""

    @staticmethod
    def section(title: str, width: int = 60) -> str:
        """生成标题段

        Args:
            title: 标题
            width: 宽度

        Returns:
            str: 格式化的标题
        """
        return f"{title}\n{'='*width}\n"

    @staticmethod
    def subsection(title: str, width: int = 60) -> str:
        """生成子标题段

        Args:
            title: 标题
            width: 宽度

        Returns:
            str: 格式化的子标题
        """
        return f"\n{title}\n{'-'*width}\n"

    @staticmethod
    def build(parts: list[str]) -> str:
        """构建返回值

        Args:
            parts: 内容部分列表

        Returns:
            str: 组合的返回值
        """
        return "".join(parts)

    @staticmethod
    def error(message: str) -> str:
        """生成错误返回值

        Args:
            message: 错误信息

        Returns:
            str: 格式化的错误信息
        """
        return f"❌ {message}"

    @staticmethod
    def success(message: str) -> str:
        """生成成功返回值

        Args:
            message: 成功信息

        Returns:
            str: 格式化的成功信息
        """
        return f"✅ {message}"

    @staticmethod
    def warning(message: str) -> str:
        """生成警告返回值

        Args:
            message: 警告信息

        Returns:
            str: 格式化的警告信息
        """
        return f"⚠️ {message}"


class ExceptionHandler:
    """异常处理工具类"""

    @staticmethod
    def handle_validation_error(func_name: str, error: ValidationError) -> str:
        """处理验证错误

        Args:
            func_name: 函数名
            error: 异常对象

        Returns:
            str: 错误返回值
        """
        error_msg = f"参数验证失败: {str(error)}"
        logger.error(f"[{func_name}] {error_msg}")
        return ResponseFormatter.error(error_msg)

    @staticmethod
    def handle_runtime_error(func_name: str, error: Exception) -> str:
        """处理运行时错误

        Args:
            func_name: 函数名
            error: 异常对象

        Returns:
            str: 错误返回值
        """
        if isinstance(error, (ValueError, RuntimeError)):
            error_msg = str(error)
            logger.error(f"[{func_name}] {error_msg}")
            return ResponseFormatter.error(error_msg)
        else:
            error_msg = f"未预期的错误: {type(error).__name__}: {str(error)}"
            logger.exception(f"[{func_name}] {error_msg}")
            return ResponseFormatter.error(error_msg)


class CacheEntry(Generic[T]):
    """缓存条目"""

    def __init__(self, value: T, ttl_seconds: int = 1800):
        """初始化缓存条目

        Args:
            value: 缓存值
            ttl_seconds: 生存时间（秒），默认30分钟
        """
        self.value = value
        self.timestamp = datetime.now(timezone.utc)
        self.ttl = timedelta(seconds=ttl_seconds)

    def is_expired(self) -> bool:
        """检查缓存是否过期

        Returns:
            bool: 是否过期
        """
        return (datetime.now(timezone.utc) - self.timestamp) > self.ttl

    def get_age_seconds(self) -> int:
        """获取缓存年龄（秒）

        Returns:
            int: 缓存年龄
        """
        return int((datetime.now(timezone.utc) - self.timestamp).total_seconds())


class LRUCache(Generic[T]):
    """带容量限制和 TTL 的 LRU 缓存

    Features:
    - 容量限制（默认 100 个条目）
    - TTL 支持（可配置的生存时间）
    - LRU 清理（超容量时删除最少使用的条目）
    - 自动过期清理
    """

    def __init__(self, max_size: int = 100, ttl_seconds: int = 1800):
        """初始化 LRU 缓存

        Args:
            max_size: 最大缓存条目数，默认 100
            ttl_seconds: TTL 生存时间（秒），默认 30 分钟
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()

    def get(self, key: str) -> Optional[T]:
        """获取缓存值

        Args:
            key: 缓存键

        Returns:
            T: 缓存值，如果不存在或已过期则返回 None
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]

        # 检查是否过期
        if entry.is_expired():
            del self._cache[key]
            logger.debug(f"🗑️ 缓存已过期，删除: {key}")
            return None

        # 移到末尾（标记为最近使用）
        self._cache.move_to_end(key)
        logger.debug(f"✅ 从缓存返回: {key} (年龄: {entry.get_age_seconds()}s)")
        return entry.value

    def set(self, key: str, value: T) -> None:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
        """
        # 如果键已存在，先删除（重新排序）
        if key in self._cache:
            del self._cache[key]

        # 添加新条目
        self._cache[key] = CacheEntry(value, self.ttl_seconds)

        # 如果超过容量，删除最少使用的条目
        while len(self._cache) > self.max_size:
            removed_key, removed_entry = self._cache.popitem(last=False)
            logger.info(
                f"🗑️ 缓存已满，删除最少使用的条目: {removed_key} (年龄: {removed_entry.get_age_seconds()}s)"
            )

        logger.debug(f"💾 缓存已设置: {key} (容量: {len(self._cache)}/{self.max_size})")

    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        logger.info("🗑️ 缓存已清空")

    def cleanup_expired(self) -> int:
        """清理所有过期的缓存条目

        Returns:
            int: 清理的条目数
        """
        expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.info(f"🗑️ 清理了 {len(expired_keys)} 个过期的缓存条目")

        return len(expired_keys)

    def get_stats(self) -> dict:
        """获取缓存统计信息

        Returns:
            dict: 统计信息
        """
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "usage_percent": round((len(self._cache) / self.max_size) * 100, 1),
        }


def validate_and_handle(func_name: str) -> Callable:
    """装饰器：参数验证和异常处理

    使用方式：
    @validate_and_handle("my_function")
    async def my_function(...) -> str:
        # 函数内如果需要参数验证，抛出 ValidationError
        # 其他异常会被自动捕获

    Args:
        func_name: 函数名

    Returns:
        Callable: 装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> str:
            try:
                return await func(*args, **kwargs)
            except ValidationError as e:
                return ExceptionHandler.handle_validation_error(func_name, e)
            except Exception as e:
                return ExceptionHandler.handle_runtime_error(func_name, e)

        return async_wrapper

    return decorator


# 快速验证和返回错误的便捷函数
def quick_validate_github_url(github_url: Any) -> Optional[str]:
    """快速验证 GitHub URL，如果无效返回错误信息

    Args:
        github_url: GitHub URL

    Returns:
        str: 错误信息（如果无效）或 None（如果有效）
    """
    try:
        ParameterValidator.validate_github_url(github_url)
        return None
    except ValidationError as e:
        return ResponseFormatter.error(str(e))

