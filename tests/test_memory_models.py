"""
单元测试：测试 memory_models.py 的数据模型

注意：此测试文件已更新以匹配当前 memory_models.py 的结构
由于 Metadata 类有必填参数，部分模型测试需要显式提供 metadata
"""

import pytest
from datetime import datetime
from typing import Any, Dict

from agentic_layer.memory_models import (
    MemoryType,
    RetrieveMethod,
    ForesightModel,
    CoreMemoryModel,
    Metadata,
)


# ==================== 辅助函数 ====================

def create_test_metadata(memory_type: str = "test") -> Metadata:
    """创建测试用的 Metadata 对象"""
    return Metadata(source="test_source", user_id="test_user", memory_type=memory_type)


# ==================== 枚举类型测试 ====================

class TestMemoryType:
    """测试记忆类型枚举"""

    def test_memory_type_values(self):
        """测试记忆类型枚举值"""
        # 基础类型
        assert MemoryType.BASE_MEMORY == "base_memory"
        assert MemoryType.PROFILE == "profile"
        assert MemoryType.PREFERENCE == "preference"
        
        # 核心/多类型
        assert MemoryType.MULTIPLE == "multiple"
        assert MemoryType.CORE == "core"
        
        # 情景和前瞻
        assert MemoryType.EPISODIC_MEMORY == "episodic_memory"
        assert MemoryType.FORESIGHT == "foresight"
        
        # 实体和关系
        assert MemoryType.ENTITY == "entity"
        assert MemoryType.RELATION == "relation"
        
        # 行为历史
        assert MemoryType.BEHAVIOR_HISTORY == "behavior_history"
        
        # 个人前瞻和事件日志
        assert MemoryType.PERSONAL_FORESIGHT == "personal_foresight"
        assert MemoryType.PERSONAL_EVENT_LOG == "personal_event_log"
        
        # 群组画像
        assert MemoryType.GROUP_PROFILE == "group_profile"

    def test_memory_type_count(self):
        """测试记忆类型数量"""
        # 当前共有 13 种记忆类型
        assert len(MemoryType) == 13

    def test_foresight_renamed_correctly(self):
        """测试 semantic_memory 已正确重命名为 foresight"""
        # 确保新名称存在
        assert hasattr(MemoryType, 'FORESIGHT')
        assert hasattr(MemoryType, 'PERSONAL_FORESIGHT')
        
        # 确保旧名称不存在（重构验证）
        assert not hasattr(MemoryType, 'SEMANTIC_MEMORY')
        assert not hasattr(MemoryType, 'PERSONAL_SEMANTIC_MEMORY')

    def test_memory_type_is_string_enum(self):
        """测试 MemoryType 是字符串枚举"""
        assert MemoryType.FORESIGHT.value == "foresight"
        assert str(MemoryType.FORESIGHT) == "MemoryType.FORESIGHT"
        # 作为字符串枚举，可以直接比较
        assert MemoryType.FORESIGHT == "foresight"


class TestRetrieveMethod:
    """测试检索方法枚举"""

    def test_retrieve_method_values(self):
        """测试检索方法枚举值"""
        assert RetrieveMethod.KEYWORD == "keyword"
        assert RetrieveMethod.VECTOR == "vector"
        assert RetrieveMethod.HYBRID == "hybrid"

    def test_retrieve_method_count(self):
        """测试检索方法数量"""
        assert len(RetrieveMethod) == 3


# ==================== Metadata 测试 ====================

class TestMetadata:
    """测试元数据类"""

    def test_create_metadata(self):
        """测试创建元数据"""
        metadata = Metadata(
            source="test_source",
            user_id="user_001",
            memory_type="profile"
        )
        
        assert metadata.source == "test_source"
        assert metadata.user_id == "user_001"
        assert metadata.memory_type == "profile"

    def test_metadata_optional_fields(self):
        """测试元数据可选字段"""
        metadata = Metadata(
            source="test",
            user_id="user_001",
            memory_type="base_memory",
            limit=10,
            email="test@example.com",
            phone="1234567890",
            full_name="Test User"
        )
        
        assert metadata.limit == 10
        assert metadata.email == "test@example.com"
        assert metadata.phone == "1234567890"
        assert metadata.full_name == "Test User"

    def test_metadata_to_dict(self):
        """测试元数据转字典"""
        metadata = Metadata(
            source="test",
            user_id="user_001",
            memory_type="profile",
            limit=5
        )
        
        result = metadata.to_dict()
        assert result["source"] == "test"
        assert result["user_id"] == "user_001"
        assert result["memory_type"] == "profile"
        assert result["limit"] == 5
        # None 值不应出现在字典中
        assert "email" not in result

    def test_metadata_from_dict(self):
        """测试从字典创建元数据"""
        data = {
            "source": "api",
            "user_id": "user_002",
            "memory_type": "episodic_memory"
        }
        
        metadata = Metadata.from_dict(data)
        assert metadata.source == "api"
        assert metadata.user_id == "user_002"
        assert metadata.memory_type == "episodic_memory"

    def test_metadata_required_fields(self):
        """测试元数据必填字段验证"""
        # 缺少必填字段应该抛出 TypeError
        with pytest.raises(TypeError):
            Metadata(source="test")  # 缺少 user_id 和 memory_type


# ==================== ForesightModel 测试（重构验证）====================

class TestForesightModel:
    """测试前瞻模型（原 SemanticMemoryModel）"""

    def test_create_foresight_model(self):
        """测试创建前瞻模型"""
        model = ForesightModel(
            id="foresight_001",
            user_id="user_001",
            concept="机器学习",
            definition="让计算机从数据中学习的技术",
            category="技术概念",
            related_concepts=["人工智能", "深度学习"],
            source="学习笔记",
            metadata=create_test_metadata("foresight"),
        )

        assert model.id == "foresight_001"
        assert model.user_id == "user_001"
        assert model.concept == "机器学习"
        assert model.definition == "让计算机从数据中学习的技术"
        assert model.category == "技术概念"
        assert model.related_concepts == ["人工智能", "深度学习"]
        assert model.source == "学习笔记"

    def test_foresight_model_default_fields(self):
        """测试前瞻模型默认字段"""
        model = ForesightModel(
            id="foresight_001",
            user_id="user_001",
            concept="测试概念",
            definition="测试定义",
            category="测试类别",
            metadata=create_test_metadata("foresight"),
        )

        assert model.related_concepts == []
        assert model.confidence_score == 1.0
        assert model.source is None

    def test_foresight_model_class_name(self):
        """验证类名已从 SemanticMemoryModel 重命名为 ForesightModel"""
        assert ForesightModel.__name__ == "ForesightModel"


# ==================== CoreMemoryModel 测试 ====================

class TestCoreMemoryModel:
    """测试核心记忆模型"""

    def test_create_core_memory_model(self):
        """测试创建核心记忆模型"""
        model = CoreMemoryModel(
            id="core_001",
            user_id="user_001",
            version="v1.0",
            is_latest=True,
            user_name="张三",
            gender="male",
            position="工程师",
            department="技术部",
            metadata=create_test_metadata("core"),
        )

        assert model.id == "core_001"
        assert model.user_id == "user_001"
        assert model.version == "v1.0"
        assert model.is_latest is True
        assert model.user_name == "张三"
        assert model.gender == "male"
        assert model.position == "工程师"
        assert model.department == "技术部"

    def test_core_memory_model_optional_fields(self):
        """测试核心记忆模型可选字段"""
        model = CoreMemoryModel(
            id="core_001",
            user_id="user_001",
            version="v1.0",
            is_latest=True,
            metadata=create_test_metadata("core"),
        )

        assert model.user_name is None
        assert model.supervisor_user_id is None
        assert model.team_members is None
        assert model.okr is None
        assert model.hard_skills is None
        assert model.soft_skills is None
        assert model.personality is None
        assert model.extend is None


# ==================== 重构验证测试 ====================

class TestSemanticToForesightRefactor:
    """
    验证 semantic_memory → foresight 重构的测试
    
    确保：
    1. 新名称存在且正确
    2. 旧名称已被移除
    3. API 值正确
    """

    def test_memory_type_foresight_value(self):
        """测试 MemoryType.FORESIGHT 的值"""
        assert MemoryType.FORESIGHT.value == "foresight"

    def test_memory_type_personal_foresight_value(self):
        """测试 MemoryType.PERSONAL_FORESIGHT 的值"""
        assert MemoryType.PERSONAL_FORESIGHT.value == "personal_foresight"

    def test_no_semantic_memory_in_memory_type(self):
        """确保 MemoryType 中没有 SEMANTIC_MEMORY"""
        memory_type_names = [m.name for m in MemoryType]
        assert "SEMANTIC_MEMORY" not in memory_type_names
        assert "PERSONAL_SEMANTIC_MEMORY" not in memory_type_names

    def test_foresight_in_memory_type(self):
        """确保 MemoryType 中有 FORESIGHT"""
        memory_type_names = [m.name for m in MemoryType]
        assert "FORESIGHT" in memory_type_names
        assert "PERSONAL_FORESIGHT" in memory_type_names

    def test_foresight_model_exists(self):
        """确保 ForesightModel 类存在"""
        assert ForesightModel is not None
        assert callable(ForesightModel)


if __name__ == "__main__":
    pytest.main([__file__])
