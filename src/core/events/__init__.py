# -*- coding: utf-8 -*-
"""
事件模块

提供应用级事件发布/订阅机制，支持：
- 事件基类 (BaseEvent): 所有业务事件的基类，支持 JSON/BSON 序列化
- 事件监听器 (EventListener): 事件监听器抽象基类
- 事件发布器 (ApplicationEventPublisher): 全局事件发布器

使用示例:

1. 定义事件:
    >>> from dataclasses import dataclass
    >>> from core.events import BaseEvent
    >>>
    >>> @dataclass
    ... class UserCreatedEvent(BaseEvent):
    ...     user_id: str
    ...     username: str
    ...
    ...     @classmethod
    ...     def from_dict(cls, data):
    ...         return cls(
    ...             event_id=data.get("event_id"),
    ...             created_at=data.get("created_at"),
    ...             user_id=data["user_id"],
    ...             username=data["username"],
    ...         )

2. 定义监听器:
    >>> from core.di import component
    >>> from core.events import EventListener, BaseEvent
    >>>
    >>> @component("user_event_listener")
    ... class UserEventListener(EventListener):
    ...     def get_event_types(self):
    ...         return [UserCreatedEvent]
    ...
    ...     async def on_event(self, event: BaseEvent):
    ...         print(f"用户创建: {event.user_id}")

3. 发布事件:
    >>> from core.di import get_bean_by_type
    >>> from core.events import ApplicationEventPublisher
    >>>
    >>> publisher = get_bean_by_type(ApplicationEventPublisher)
    >>> await publisher.publish(UserCreatedEvent(user_id="123", username="alice"))
"""

from core.events.base_event import BaseEvent
from core.events.event_listener import EventListener
from core.events.event_publisher import ApplicationEventPublisher

__all__ = ['BaseEvent', 'EventListener', 'ApplicationEventPublisher']
