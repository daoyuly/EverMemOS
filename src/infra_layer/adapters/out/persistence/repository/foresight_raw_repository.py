"""
Foresight 原生 CRUD 仓库

基于 Beanie ODM 的前瞻原生数据访问层，提供完整的 CRUD 操作。
不依赖领域层接口，直接操作 Foresight 文档模型。
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClientSession
from core.observation.logger import get_logger
from core.di.decorators import repository
from core.oxm.mongo.base_repository import BaseRepository

from infra_layer.adapters.out.persistence.document.memory.foresight import (
    Foresight,
)

logger = get_logger(__name__)


@repository("foresight_raw_repository", primary=True)
class ForesightRawRepository(BaseRepository[Foresight]):
    """
    前瞻原生 CRUD 仓库

    提供对前瞻文档的直接数据库操作，包括：
    - 基本 CRUD 操作（继承自 BaseRepository）
    - 文本搜索和查询
    - 来源链接管理
    - 统计和聚合查询
    - 事务管理（继承自 BaseRepository）
    """

    def __init__(self):
        """初始化仓库"""
        super().__init__(Foresight)

    async def get_by_user_id(self, user_id: str) -> Optional[Foresight]:
        """
        根据用户ID获取前瞻

        Args:
            user_id: 用户ID

        Returns:
            Foresight 实例或 None
        """
        try:
            return await self.model.find_one({"user_id": user_id})
        except Exception as e:
            logger.error("❌ 根据用户ID获取前瞻失败: %s", e)
            return None

    async def update_by_user_id(
        self,
        user_id: str,
        update_data: Dict[str, Any],
        session: Optional[AsyncIOMotorClientSession] = None,
    ) -> Optional[Foresight]:
        """
        根据用户ID更新前瞻

        Args:
            user_id: 用户ID
            update_data: 更新数据字典
            session: 可选的 MongoDB 会话，用于事务支持

        Returns:
            更新后的 Foresight 实例或 None
        """
        try:
            foresight = await self.get_by_user_id(user_id)
            if foresight:
                for key, value in update_data.items():
                    if hasattr(foresight, key):
                        setattr(foresight, key, value)
                await foresight.save(session=session)
                logger.debug("✅ 根据用户ID更新前瞻成功: %s", user_id)
                return foresight
            return None
        except Exception as e:
            logger.error("❌ 根据用户ID更新前瞻失败: %s", e)
            raise e

    async def delete_by_user_id(
        self, user_id: str, session: Optional[AsyncIOMotorClientSession] = None
    ) -> bool:
        """
        根据用户ID删除前瞻

        Args:
            user_id: 用户ID
            session: 可选的 MongoDB 会话，用于事务支持

        Returns:
            删除成功返回 True，否则返回 False
        """
        try:
            foresight = await self.get_by_user_id(user_id)
            if foresight:
                await foresight.delete(session=session)
                logger.info("✅ 根据用户ID删除前瞻成功: %s", user_id)
                return True
            return False
        except Exception as e:
            logger.error("❌ 根据用户ID删除前瞻失败: %s", e)
            return False


# 导出
__all__ = ["ForesightRawRepository"]
