from typing import Dict, Any
from abc import ABC, abstractmethod
import uuid
from fastapi import Request

from core.di.decorators import component
from core.observation.logger import get_logger

logger = get_logger(__name__)


class AppLogicProvider(ABC):
    """应用逻辑提供者接口，负责从请求中提取应用级别的上下文信息及处理应用逻辑"""

    @abstractmethod
    async def provide(self, request: Request) -> Dict[str, Any]:
        """
        处理请求并提供应用级别的上下文数据

        Args:
            request: FastAPI请求对象

        Returns:
            Dict[str, Any]: 包含所有上下文数据的字典
        """
        raise NotImplementedError


@component(name="app_logic_provider")
class AppLogicProviderImpl(AppLogicProvider):
    """应用逻辑提供者实现，负责从请求中提取应用级别的上下文信息"""

    async def provide(self, request: Request) -> Dict[str, Any]:
        """
        处理请求并提供应用级别的上下文数据

        Args:
            request: FastAPI请求对象

        Returns:
            Dict[str, Any]: 包含所有上下文数据的字典，包括request_id
        """
        # 创建新的app_info字典
        app_info = {}

        # 从请求头中获取request_id，优先X-Request-Id，兼容小写
        request_id = request.headers.get('X-Request-Id') or request.headers.get(
            'x-request-id'
        )
        if not request_id:
            request_id = str(uuid.uuid4())

        app_info['request_id'] = request_id

        return app_info
