# -*- coding: utf-8 -*-
"""
应用事件发布器模块

提供全局的事件发布机制，支持异步并发分发事件到多个监听器。
通过 DI 容器自动发现和注册所有 EventListener 实现。
"""

import asyncio
from typing import Dict, List, Set, Type, Optional

from core.di import service, get_beans_by_type
from core.events.base_event import BaseEvent
from core.events.event_listener import EventListener
from core.observation.logger import get_logger


logger = get_logger(__name__)


@service("application_event_publisher")
class ApplicationEventPublisher:
    """
    应用事件发布器

    全局单例服务，负责将事件分发到对应的监听器。
    通过 DI 容器自动发现所有 EventListener 实现，并构建事件类型到监听器的映射。

    特性：
    - 懒加载：首次发布事件时才构建监听器映射
    - 异步并发：使用 asyncio.gather 并发调用所有匹配的监听器
    - 错误隔离：单个监听器的异常不会影响其他监听器
    - 可刷新：支持动态刷新监听器映射

    使用方式：
    1. 通过 DI 获取实例：
        >>> from core.di import get_bean_by_type
        >>> publisher = get_bean_by_type(ApplicationEventPublisher)

    2. 发布事件：
        >>> await publisher.publish(UserCreatedEvent(user_id="123"))

    3. 同步发布（在非异步上下文中）：
        >>> publisher.publish_sync(UserCreatedEvent(user_id="123"))
    """

    def __init__(self):
        """初始化事件发布器"""
        # 事件类型 -> 监听器列表的映射
        self._event_listeners_map: Dict[Type[BaseEvent], List[EventListener]] = {}
        # 是否已初始化
        self._initialized: bool = False
        # 所有监听器实例
        self._listeners: List[EventListener] = []

    def _ensure_initialized(self) -> None:
        """
        确保监听器映射已初始化

        懒加载机制：首次调用时才从 DI 容器获取所有监听器并构建映射。
        """
        if self._initialized:
            return

        self._build_listener_mapping()
        self._initialized = True

    def _build_listener_mapping(self) -> None:
        """
        构建事件类型到监听器的映射

        从 DI 容器获取所有 EventListener 实例，
        然后根据每个监听器声明的事件类型构建映射表。
        """
        # 清空现有映射
        self._event_listeners_map.clear()
        self._listeners.clear()

        # 从 DI 容器获取所有 EventListener 实现
        try:
            listeners = get_beans_by_type(EventListener)
        except Exception as e:
            logger.warning(f"获取 EventListener 实例失败: {e}")
            listeners = []

        self._listeners = listeners

        # 构建事件类型到监听器的映射
        for listener in listeners:
            listener_name = listener.get_listener_name()
            event_types = listener.get_event_types()

            logger.debug(
                f"注册监听器 [{listener_name}]，监听事件类型: {[et.__name__ for et in event_types]}"
            )

            for event_type in event_types:
                if event_type not in self._event_listeners_map:
                    self._event_listeners_map[event_type] = []
                self._event_listeners_map[event_type].append(listener)

        # 记录初始化完成日志
        total_listeners = len(listeners)
        total_event_types = len(self._event_listeners_map)
        logger.info(
            f"事件发布器初始化完成: {total_listeners} 个监听器, {total_event_types} 个事件类型"
        )

    def refresh(self) -> None:
        """
        刷新监听器映射

        当有新的监听器注册到 DI 容器后，可调用此方法刷新映射。
        """
        self._initialized = False
        self._ensure_initialized()
        logger.info("事件发布器监听器映射已刷新")

    def get_listeners_for_event(
        self, event_type: Type[BaseEvent]
    ) -> List[EventListener]:
        """
        获取指定事件类型的所有监听器

        Args:
            event_type: 事件类型

        Returns:
            List[EventListener]: 监听该事件类型的所有监听器列表
        """
        self._ensure_initialized()
        return self._event_listeners_map.get(event_type, [])

    def get_all_listeners(self) -> List[EventListener]:
        """
        获取所有已注册的监听器

        Returns:
            List[EventListener]: 所有监听器列表
        """
        self._ensure_initialized()
        return self._listeners.copy()

    def get_registered_event_types(self) -> Set[Type[BaseEvent]]:
        """
        获取所有已注册监听的事件类型

        Returns:
            Set[Type[BaseEvent]]: 事件类型集合
        """
        self._ensure_initialized()
        return set(self._event_listeners_map.keys())

    async def publish(self, event: BaseEvent) -> None:
        """
        异步发布事件

        将事件分发到所有监听该事件类型的监听器。
        使用 asyncio.gather 并发调用所有监听器，提高 IO 密集型操作的效率。

        单个监听器的异常不会影响其他监听器的执行，
        所有异常都会被记录到日志中。

        Args:
            event: 要发布的事件对象
        """
        self._ensure_initialized()

        event_type = type(event)
        event_type_name = event.event_type()
        listeners = self._event_listeners_map.get(event_type, [])

        if not listeners:
            logger.debug(f"事件 [{event_type_name}] 没有监听器，跳过发布")
            return

        logger.debug(
            f"发布事件 [{event_type_name}] (id={event.event_id})，共 {len(listeners)} 个监听器"
        )

        # 创建所有监听器的协程任务
        async def safe_invoke(listener: EventListener) -> Optional[Exception]:
            """
            安全地调用监听器，捕获异常避免影响其他监听器

            Returns:
                如果发生异常返回异常对象，否则返回 None
            """
            try:
                await listener.on_event(event)
                return None
            except Exception as e:
                listener_name = listener.get_listener_name()
                logger.error(
                    f"监听器 [{listener_name}] 处理事件 [{event_type_name}] 时发生异常: {e}",
                    exc_info=True,
                )
                return e

        # 并发执行所有监听器
        tasks = [safe_invoke(listener) for listener in listeners]
        results = await asyncio.gather(*tasks)

        # 统计执行结果
        errors = [r for r in results if r is not None]
        if errors:
            logger.warning(
                f"事件 [{event_type_name}] 发布完成，"
                f"成功: {len(listeners) - len(errors)}, 失败: {len(errors)}"
            )
        else:
            logger.debug(
                f"事件 [{event_type_name}] 发布完成，所有 {len(listeners)} 个监听器执行成功"
            )

    def publish_sync(self, event: BaseEvent) -> None:
        """
        同步发布事件

        在非异步上下文中使用此方法发布事件。
        内部会创建或使用现有的事件循环来执行异步发布。

        注意：如果当前已在异步上下文中，应优先使用 `publish()` 方法。

        Args:
            event: 要发布的事件对象
        """
        try:
            # 尝试获取当前运行的事件循环
            loop = asyncio.get_running_loop()
            # 如果在异步上下文中，创建一个任务
            loop.create_task(self.publish(event))
        except RuntimeError:
            # 没有运行的事件循环，创建新的运行
            asyncio.run(self.publish(event))

    async def publish_batch(self, events: List[BaseEvent]) -> None:
        """
        批量发布多个事件

        并发发布多个事件，提高批量操作的效率。

        Args:
            events: 要发布的事件列表
        """
        if not events:
            return

        logger.debug(f"批量发布 {len(events)} 个事件")

        # 并发发布所有事件
        tasks = [self.publish(event) for event in events]
        await asyncio.gather(*tasks)

        logger.debug(f"批量发布完成，共 {len(events)} 个事件")

    def __repr__(self) -> str:
        """返回对象的字符串表示"""
        self._ensure_initialized()
        return (
            f"ApplicationEventPublisher("
            f"listeners={len(self._listeners)}, "
            f"event_types={len(self._event_listeners_map)}"
            f")"
        )
