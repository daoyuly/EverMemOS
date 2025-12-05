# -*- coding: utf-8 -*-
"""
请求日志 Kafka 监听器

监听 RequestLogEvent 事件，并将其发送到 Kafka 进行后续处理。
当前实现为简单的打印输出，后续可扩展为实际的 Kafka 发送逻辑。
"""

from typing import List, Type

from core.di import component
from core.events import BaseEvent, EventListener
from core.observation.logger import get_logger
from infra_layer.adapters.out.event.request_log import RequestLogEvent


logger = get_logger(__name__)


@component("request_log_kafka_listener")
class RequestLogKafkaListener(EventListener):
    """
    请求日志 Kafka 监听器

    监听 RequestLogEvent 事件，负责将请求日志发送到 Kafka。
    当前实现仅打印日志，后续可替换为实际的 Kafka Producer 逻辑。

    使用方式：
    监听器会被 ApplicationEventPublisher 自动发现和注册，
    当 RequestLogEvent 被发布时，on_event 方法会被自动调用。
    """

    def __init__(self):
        """初始化监听器"""
        # 后续可在此处初始化 Kafka Producer
        self._kafka_topic = "request-log-events"
        logger.info(
            "RequestLogKafkaListener 初始化完成，目标 topic: %s", self._kafka_topic
        )

    def get_event_types(self) -> List[Type[BaseEvent]]:
        """
        获取要监听的事件类型列表

        Returns:
            List[Type[BaseEvent]]: 监听的事件类型列表
        """
        return [RequestLogEvent]

    async def on_event(self, event: BaseEvent) -> None:
        """
        处理 RequestLogEvent 事件

        当前实现为简单的打印输出，后续可替换为实际的 Kafka 发送逻辑。

        Args:
            event: 接收到的事件对象
        """
        if not isinstance(event, RequestLogEvent):
            logger.warning(
                "收到非 RequestLogEvent 类型的事件: %s", type(event).__name__
            )
            return

        # 打印事件信息（后续替换为 Kafka 发送逻辑）
        print("[RequestLogKafkaListener] 收到请求日志事件:")
        print(f"  - event_id: {event.event_id}")
        print(f"  - request_id: {event.request_id}")
        print(f"  - method: {event.method}")
        print(f"  - url: {event.url}")
        print(f"  - http_code: {event.http_code}")
        print(f"  - time_ms: {event.time_ms}")
        print(f"  - status: {event.status}")
        if event.error_message:
            print(f"  - error_message: {event.error_message}")

        logger.debug(
            "RequestLogEvent 已处理: request_id=%s, url=%s", event.request_id, event.url
        )

    async def _send_to_kafka(self, event: RequestLogEvent) -> None:
        """
        发送事件到 Kafka (待实现)

        Args:
            event: 要发送的事件
        """
        # 预留: 实现 Kafka Producer 逻辑
        # kafka_message = event.to_json_str()
        # await self._producer.send(self._kafka_topic, kafka_message)
        _ = event  # 避免未使用参数警告
