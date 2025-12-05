"""
Redis 租户键工具函数模块

提供 Redis 键名的租户隔离功能，通过在 key 前拼接租户 ID 实现多租户数据隔离。
"""

from typing import Optional

from core.tenants.tenant_contextvar import get_current_tenant_id


def patch_redis_tenant_key(key: str) -> str:
    """
    为 Redis 键名添加租户前缀

    从当前上下文中获取租户 ID，并将其拼接到 key 前面，实现多租户数据隔离。
    如果当前没有设置租户信息，则返回原始 key。

    格式：{tenant_id}:{key}

    Args:
        key: 原始的 Redis 键名

    Returns:
        str: 带租户前缀的 Redis 键名，如果无租户则返回原始键名

    Examples:
        >>> # 假设当前租户 ID 为 "tenant_001"
        >>> patch_redis_tenant_key("conversation_data:group_123")
        'tenant_001:conversation_data:group_123'

        >>> # 如果没有设置租户
        >>> patch_redis_tenant_key("conversation_data:group_123")
        'conversation_data:group_123'
    """
    tenant_id: Optional[str] = get_current_tenant_id()

    if tenant_id:
        # 有租户 ID 时，拼接租户前缀
        return f"{tenant_id}:{key}"

    # 没有租户 ID 时，返回原始 key
    return key
