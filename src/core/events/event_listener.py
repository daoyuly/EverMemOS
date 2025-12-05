# -*- coding: utf-8 -*-
"""
事件监听器模块

提供事件监听器的抽象基类，支持声明式地注册要监听的事件类型。
业务监听器应该继承此基类，并实现 `get_event_types` 和 `on_event` 方法。
"""

from abc import ABC, abstractmethod
from typing import List, Set, Type

from core.events.base_event import BaseEvent


class EventListener(ABC):
    """
    事件监听器抽象基类

    业务监听器应该继承此类，并实现以下方法：
    - `get_event_types()`: 返回要监听的事件类型列表
    - `on_event(event)`: 处理事件的具体逻辑（异步方法）

    监听器会被 ApplicationEventPublisher 自动发现和注册。
    建议使用 @component 或 @service 装饰器将监听器注册到 DI 容器。

    Example:
        >>> from core.di import component
        >>>
        >>> @component("user_event_listener")
        ... class UserEventListener(EventListener):
        ...     def get_event_types(self) -> List[Type[BaseEvent]]:
        ...         return [UserCreatedEvent, UserUpdatedEvent]
        ...
        ...     async def on_event(self, event: BaseEvent) -> None:
        ...         if isinstance(event, UserCreatedEvent):
        ...             await self._handle_user_created(event)
        ...         elif isinstance(event, UserUpdatedEvent):
        ...             await self._handle_user_updated(event)
    """

    @abstractmethod
    def get_event_types(self) -> List[Type[BaseEvent]]:
        """
        获取要监听的事件类型列表

        返回此监听器关心的事件类型列表。当这些类型的事件被发布时，
        监听器的 `on_event` 方法会被调用。

        Returns:
            List[Type[BaseEvent]]: 要监听的事件类型列表

        Example:
            >>> def get_event_types(self) -> List[Type[BaseEvent]]:
            ...     return [UserCreatedEvent, OrderCreatedEvent]
        """
        pass

    @abstractmethod
    async def on_event(self, event: BaseEvent) -> None:
        """
        处理事件

        当监听的事件被发布时，此方法会被异步调用。
        实现此方法来处理具体的业务逻辑。

        注意：
        - 此方法是异步的，可以执行 IO 操作
        - 多个监听器会并发执行，互不阻塞
        - 建议在此方法内部捕获异常，避免影响其他监听器

        Args:
            event: 接收到的事件对象
        """
        pass

    def get_listener_name(self) -> str:
        """
        获取监听器名称

        默认返回类名。子类可重写此方法来自定义名称。

        Returns:
            str: 监听器名称
        """
        return self.__class__.__name__

    def get_event_type_set(self) -> Set[Type[BaseEvent]]:
        """
        获取要监听的事件类型集合（内部使用）

        返回事件类型的集合，用于快速查找。

        Returns:
            Set[Type[BaseEvent]]: 事件类型集合
        """
        return set(self.get_event_types())
