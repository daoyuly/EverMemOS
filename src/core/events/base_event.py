# -*- coding: utf-8 -*-
"""
事件基类模块

提供事件的基础抽象类，支持 JSON 和 BSON 序列化/反序列化。
所有业务事件都应该继承此基类。
"""

import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Type, TypeVar

import bson

from common_utils.datetime_utils import get_now_with_timezone, to_iso_format


T = TypeVar('T', bound='BaseEvent')


@dataclass
class BaseEvent(ABC):
    """
    事件基类

    所有业务事件都应该继承此类。子类需要定义自己的业务字段，
    并可选择性地重写 `event_type` 方法来自定义事件类型名称。

    基类提供以下功能：
    - 自动生成事件ID (event_id)
    - 自动记录事件创建时间 (created_at)
    - JSON 序列化/反序列化
    - BSON 序列化/反序列化

    Attributes:
        event_id: 事件唯一标识符，自动生成
        created_at: 事件创建时间（ISO 格式字符串），自动生成

    Example:
        >>> @dataclass
        ... class UserCreatedEvent(BaseEvent):
        ...     user_id: str
        ...     username: str
        ...
        >>> event = UserCreatedEvent(user_id="123", username="alice")
        >>> print(event.event_type())  # "UserCreatedEvent"
        >>> json_str = event.to_json_str()
        >>> restored = UserCreatedEvent.from_json_str(json_str)
    """

    # 基类字段，使用 field 提供默认值工厂
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(
        default_factory=lambda: to_iso_format(get_now_with_timezone())
    )

    @classmethod
    def event_type(cls) -> str:
        """
        获取事件类型名称

        默认返回类名。子类可重写此方法来自定义事件类型名称。

        Returns:
            str: 事件类型名称
        """
        return cls.__name__

    def to_dict(self) -> Dict[str, Any]:
        """
        将对象转换为可序列化的字典

        注意：会自动添加 `_event_type` 字段，用于反序列化时确定具体的事件类型。

        Returns:
            Dict[str, Any]: 对象的字典表示
        """
        data = asdict(self)
        # 添加事件类型字段，用于反序列化时识别
        data['_event_type'] = self.event_type()
        return data

    @classmethod
    @abstractmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        从字典创建对象实例

        子类必须实现此方法，以支持反序列化。

        Args:
            data: 包含事件数据的字典

        Returns:
            事件对象实例

        Raises:
            KeyError: 缺少必要字段
            TypeError: 字段类型不正确
        """
        pass

    def to_json_str(self) -> str:
        """
        将对象序列化为 JSON 字符串

        Returns:
            str: JSON 字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def to_bson_bytes(self) -> bytes:
        """
        将对象序列化为 BSON 字节数据

        Returns:
            bytes: BSON 字节数据
        """
        return bson.encode(self.to_dict())

    @classmethod
    def from_json_str(cls: Type[T], json_str: str) -> T:
        """
        从 JSON 字符串反序列化创建对象实例

        Args:
            json_str: JSON 字符串

        Returns:
            事件对象实例

        Raises:
            ValueError: JSON 格式错误或数据无效
        """
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise ValueError(f"无效的 JSON 数据: {e}") from e

    @classmethod
    def from_bson_bytes(cls: Type[T], bson_bytes: bytes) -> T:
        """
        从 BSON 字节数据反序列化创建对象实例

        Args:
            bson_bytes: BSON 字节数据

        Returns:
            事件对象实例

        Raises:
            ValueError: BSON 格式错误或数据无效
        """
        try:
            data = bson.decode(bson_bytes)
            return cls.from_dict(data)
        except Exception as e:
            raise ValueError(f"无效的 BSON 数据: {e}") from e

    def __repr__(self) -> str:
        """返回对象的字符串表示"""
        return f"{self.__class__.__name__}(event_id={self.event_id!r}, created_at={self.created_at!r})"
