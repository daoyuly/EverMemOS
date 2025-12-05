# -*- coding: utf-8 -*-
"""
事件发布器测试

测试 ApplicationEventPublisher 的核心功能：
- 事件基类的序列化/反序列化
- 事件监听器的注册和发现
- 事件的异步发布和并发处理
"""

import asyncio
import pytest
from dataclasses import dataclass
from typing import Any, Dict, List, Type

from core.di import get_container, clear_container, register_bean, get_bean_by_type
from core.events import BaseEvent, EventListener, ApplicationEventPublisher
from infra_layer.adapters.out.event.request_log import RequestLogEvent


# ============================================================
# 测试用的事件和监听器
# ============================================================


@dataclass
class MockUserCreatedEvent(BaseEvent):
    """测试用的用户创建事件"""

    user_id: str = ""
    username: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MockUserCreatedEvent':
        return cls(
            event_id=data.get("event_id", ""),
            created_at=data.get("created_at", ""),
            user_id=data.get("user_id", ""),
            username=data.get("username", ""),
        )


@dataclass
class MockOrderCreatedEvent(BaseEvent):
    """测试用的订单创建事件"""

    order_id: str = ""
    amount: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MockOrderCreatedEvent':
        return cls(
            event_id=data.get("event_id", ""),
            created_at=data.get("created_at", ""),
            order_id=data.get("order_id", ""),
            amount=data.get("amount", 0.0),
        )


class MockEventListener(EventListener):
    """测试用的事件监听器"""

    def __init__(self):
        self.received_events: List[BaseEvent] = []

    def get_event_types(self) -> List[Type[BaseEvent]]:
        return [MockUserCreatedEvent, MockOrderCreatedEvent]

    async def on_event(self, event: BaseEvent) -> None:
        self.received_events.append(event)
        print(f"[MockEventListener] 收到事件: {event}")


class MockRequestLogListener(EventListener):
    """测试用的请求日志监听器"""

    def __init__(self):
        self.received_events: List[RequestLogEvent] = []

    def get_event_types(self) -> List[Type[BaseEvent]]:
        return [RequestLogEvent]

    async def on_event(self, event: BaseEvent) -> None:
        if isinstance(event, RequestLogEvent):
            self.received_events.append(event)
            print(
                f"[MockRequestLogListener] 收到请求日志: {event.request_id} - {event.url}"
            )


class MockFailingListener(EventListener):
    """测试用的会抛出异常的监听器"""

    def __init__(self):
        self.call_count = 0

    def get_event_types(self) -> List[Type[BaseEvent]]:
        return [MockUserCreatedEvent]

    async def on_event(self, event: BaseEvent) -> None:
        self.call_count += 1
        raise RuntimeError("模拟监听器异常")


# ============================================================
# 测试类
# ============================================================


class TestBaseEvent:
    """测试 BaseEvent 基类"""

    def test_event_has_auto_generated_fields(self):
        """测试事件自动生成 event_id 和 created_at"""
        event = MockUserCreatedEvent(user_id="123", username="alice")

        # 验证自动生成的字段
        assert event.event_id is not None
        assert len(event.event_id) > 0
        assert event.created_at is not None
        assert len(event.created_at) > 0

        print(f"event_id: {event.event_id}")
        print(f"created_at: {event.created_at}")

    def test_event_type_returns_class_name(self):
        """测试 event_type 返回类名"""
        event = MockUserCreatedEvent(user_id="123", username="alice")
        assert event.event_type() == "MockUserCreatedEvent"

    def test_event_to_dict(self):
        """测试事件转换为字典"""
        event = MockUserCreatedEvent(user_id="123", username="alice")
        data = event.to_dict()

        assert data["user_id"] == "123"
        assert data["username"] == "alice"
        assert data["_event_type"] == "MockUserCreatedEvent"
        assert "event_id" in data
        assert "created_at" in data

    def test_event_json_serialization(self):
        """测试事件 JSON 序列化和反序列化"""
        event = MockUserCreatedEvent(user_id="123", username="alice")

        # 序列化
        json_str = event.to_json_str()
        print(f"JSON: {json_str}")

        # 反序列化
        restored = MockUserCreatedEvent.from_json_str(json_str)

        assert restored.user_id == event.user_id
        assert restored.username == event.username
        assert restored.event_id == event.event_id
        assert restored.created_at == event.created_at

    def test_event_bson_serialization(self):
        """测试事件 BSON 序列化和反序列化"""
        event = MockUserCreatedEvent(user_id="456", username="bob")

        # 序列化
        bson_bytes = event.to_bson_bytes()
        print(f"BSON bytes length: {len(bson_bytes)}")

        # 反序列化
        restored = MockUserCreatedEvent.from_bson_bytes(bson_bytes)

        assert restored.user_id == event.user_id
        assert restored.username == event.username
        assert restored.event_id == event.event_id


class TestRequestLogEvent:
    """测试 RequestLogEvent"""

    def test_request_log_event_creation(self):
        """测试创建 RequestLogEvent"""
        event = RequestLogEvent(
            request_id="req-001",
            method="POST",
            url="/api/users",
            http_code=200,
            time_ms=150,
            status="success",
        )

        # 验证基类字段
        assert event.event_id is not None
        assert event.created_at is not None

        # 验证业务字段
        assert event.request_id == "req-001"
        assert event.method == "POST"
        assert event.url == "/api/users"
        assert event.http_code == 200
        assert event.time_ms == 150
        assert event.status == "success"

    def test_request_log_event_json_serialization(self):
        """测试 RequestLogEvent JSON 序列化"""
        event = RequestLogEvent(
            request_id="req-002",
            method="GET",
            url="/api/products",
            http_code=404,
            time_ms=50,
            status="not_found",
            error_message="Product not found",
        )

        # 序列化
        json_str = event.to_json_str()
        print(f"JSON: {json_str}")

        # 反序列化
        restored = RequestLogEvent.from_json_str(json_str)

        assert restored.request_id == event.request_id
        assert restored.method == event.method
        assert restored.url == event.url
        assert restored.http_code == event.http_code
        assert restored.error_message == event.error_message

    def test_request_log_event_bson_serialization(self):
        """测试 RequestLogEvent BSON 序列化"""
        event = RequestLogEvent(
            request_id="req-003",
            method="DELETE",
            url="/api/users/123",
            http_code=204,
            time_ms=30,
            status="success",
            extend={"user_agent": "TestClient/1.0"},
        )

        # 序列化
        bson_bytes = event.to_bson_bytes()

        # 反序列化
        restored = RequestLogEvent.from_bson_bytes(bson_bytes)

        assert restored.request_id == event.request_id
        assert restored.extend == {"user_agent": "TestClient/1.0"}


class TestEventPublisher:
    """测试 ApplicationEventPublisher"""

    @pytest.fixture(autouse=True)
    def setup_container(self):
        """每个测试前清空并重新设置容器"""
        clear_container()
        yield
        clear_container()

    def test_publisher_registration(self):
        """测试发布器注册到 DI 容器"""
        # 注册发布器
        register_bean(ApplicationEventPublisher)

        # 从容器获取
        publisher = get_bean_by_type(ApplicationEventPublisher)

        assert publisher is not None
        assert isinstance(publisher, ApplicationEventPublisher)

    def test_publisher_discovers_listeners(self):
        """测试发布器自动发现监听器"""
        # 创建测试监听器实例
        listener = MockEventListener()

        # 注册监听器和发布器
        register_bean(EventListener, instance=listener, name="test_event_listener")
        register_bean(ApplicationEventPublisher)

        # 获取发布器
        publisher = get_bean_by_type(ApplicationEventPublisher)

        # 验证监听器被发现
        listeners = publisher.get_all_listeners()
        assert len(listeners) == 1
        assert listeners[0] is listener

    def test_publisher_builds_event_type_mapping(self):
        """测试发布器构建事件类型映射"""
        listener = MockEventListener()

        register_bean(EventListener, instance=listener, name="test_event_listener")
        register_bean(ApplicationEventPublisher)

        publisher = get_bean_by_type(ApplicationEventPublisher)

        # 验证事件类型映射
        event_types = publisher.get_registered_event_types()
        assert MockUserCreatedEvent in event_types
        assert MockOrderCreatedEvent in event_types

    @pytest.mark.asyncio
    async def test_publish_event_to_listeners(self):
        """测试发布事件到监听器"""
        listener = MockEventListener()

        register_bean(EventListener, instance=listener, name="test_event_listener")
        register_bean(ApplicationEventPublisher)

        publisher = get_bean_by_type(ApplicationEventPublisher)

        # 发布事件
        event = MockUserCreatedEvent(user_id="123", username="alice")
        await publisher.publish(event)

        # 验证监听器收到事件
        assert len(listener.received_events) == 1
        assert listener.received_events[0].user_id == "123"
        assert listener.received_events[0].username == "alice"

    @pytest.mark.asyncio
    async def test_publish_request_log_event(self):
        """测试发布 RequestLogEvent"""
        listener = MockRequestLogListener()

        register_bean(EventListener, instance=listener, name="request_log_listener")
        register_bean(ApplicationEventPublisher)

        publisher = get_bean_by_type(ApplicationEventPublisher)

        # 发布请求日志事件
        event = RequestLogEvent(
            request_id="req-test-001",
            method="POST",
            url="/api/memories",
            http_code=201,
            time_ms=250,
            status="success",
        )
        await publisher.publish(event)

        # 验证监听器收到事件
        assert len(listener.received_events) == 1
        assert listener.received_events[0].request_id == "req-test-001"
        assert listener.received_events[0].url == "/api/memories"

    @pytest.mark.asyncio
    async def test_publish_event_with_no_listeners(self):
        """测试发布没有监听器的事件"""
        register_bean(ApplicationEventPublisher)

        publisher = get_bean_by_type(ApplicationEventPublisher)

        # 发布事件（没有监听器，应该不报错）
        event = MockUserCreatedEvent(user_id="123", username="alice")
        await publisher.publish(event)  # 不应该抛出异常

    @pytest.mark.asyncio
    async def test_listener_exception_does_not_affect_others(self):
        """测试单个监听器异常不影响其他监听器"""
        normal_listener = MockEventListener()
        failing_listener = MockFailingListener()

        register_bean(EventListener, instance=normal_listener, name="normal_listener")
        register_bean(EventListener, instance=failing_listener, name="failing_listener")
        register_bean(ApplicationEventPublisher)

        publisher = get_bean_by_type(ApplicationEventPublisher)

        # 发布事件
        event = MockUserCreatedEvent(user_id="123", username="alice")
        await publisher.publish(event)

        # 验证正常监听器收到了事件
        assert len(normal_listener.received_events) == 1
        # 验证异常监听器也被调用了
        assert failing_listener.call_count == 1

    @pytest.mark.asyncio
    async def test_publish_batch_events(self):
        """测试批量发布事件"""
        listener = MockEventListener()

        register_bean(EventListener, instance=listener, name="test_event_listener")
        register_bean(ApplicationEventPublisher)

        publisher = get_bean_by_type(ApplicationEventPublisher)

        # 批量发布事件
        events = [
            MockUserCreatedEvent(user_id="1", username="alice"),
            MockUserCreatedEvent(user_id="2", username="bob"),
            MockOrderCreatedEvent(order_id="order-1", amount=99.99),
        ]
        await publisher.publish_batch(events)

        # 验证所有事件都被接收
        assert len(listener.received_events) == 3

    @pytest.mark.asyncio
    async def test_concurrent_listeners_execution(self):
        """测试监听器并发执行"""
        # 创建多个监听器
        listeners = [MockEventListener() for _ in range(5)]

        for i, listener in enumerate(listeners):
            register_bean(EventListener, instance=listener, name=f"listener_{i}")
        register_bean(ApplicationEventPublisher)

        publisher = get_bean_by_type(ApplicationEventPublisher)

        # 发布事件
        event = MockUserCreatedEvent(user_id="concurrent-test", username="test")
        await publisher.publish(event)

        # 验证所有监听器都收到了事件
        for listener in listeners:
            assert len(listener.received_events) == 1
            assert listener.received_events[0].user_id == "concurrent-test"

    def test_publisher_refresh(self):
        """测试刷新监听器映射"""
        register_bean(ApplicationEventPublisher)

        publisher = get_bean_by_type(ApplicationEventPublisher)

        # 初始化时没有监听器
        assert len(publisher.get_all_listeners()) == 0

        # 注册新监听器
        listener = MockEventListener()
        register_bean(EventListener, instance=listener, name="new_listener")

        # 刷新映射
        publisher.refresh()

        # 验证新监听器被发现
        assert len(publisher.get_all_listeners()) == 1


class TestKafkaListenerIntegration:
    """测试 Kafka 监听器集成"""

    @pytest.fixture(autouse=True)
    def setup_container(self):
        """每个测试前清空并重新设置容器"""
        clear_container()
        yield
        clear_container()

    @pytest.mark.asyncio
    async def test_kafka_listener_receives_request_log_event(self, capsys):
        """测试 Kafka 监听器接收 RequestLogEvent"""
        # 导入并注册 Kafka 监听器
        from infra_layer.adapters.out.event.request_log_kafka_listener import (
            RequestLogKafkaListener,
        )

        register_bean(RequestLogKafkaListener)
        register_bean(ApplicationEventPublisher)

        publisher = get_bean_by_type(ApplicationEventPublisher)

        # 发布请求日志事件
        event = RequestLogEvent(
            request_id="kafka-test-001",
            method="POST",
            url="/api/test",
            http_code=200,
            time_ms=100,
            status="success",
        )
        await publisher.publish(event)

        # 捕获打印输出
        captured = capsys.readouterr()

        # 验证打印输出包含事件信息
        assert "RequestLogKafkaListener" in captured.out
        assert "kafka-test-001" in captured.out
        assert "/api/test" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
