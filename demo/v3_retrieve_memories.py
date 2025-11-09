"""V3 API 记忆检索测试

功能：
1. 测试 Episode 检索（中文查询，所有模式）
2. 测试 Event Log 检索（英文查询，所有模式）
3. 测试 Semantic Memory 检索（中文查询，所有模式）
4. 测试用户过滤
"""
import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from core.di import get_bean_by_type
from infra_layer.adapters.input.api.v3.agentic_v3_controller import AgenticV3Controller
from infra_layer.adapters.out.persistence.repository.conversation_meta_raw_repository import ConversationMetaRawRepository


class MockRequest:
    """模拟 FastAPI Request"""
    def __init__(self, data):
        self.data = data
    
    async def json(self):
        return self.data


async def test_episode_retrieval():
    """测试 Episode 检索（中文查询）"""
    print("\n" + "=" * 100)
    print("🔍 测试 Episode 检索（中文查询）")
    print("=" * 100)
    
    repository = get_bean_by_type(ConversationMetaRawRepository)
    controller = AgenticV3Controller(repository)
    
    test_cases = [
        ("北京旅游", "embedding"),
        ("北京旅游", "bm25"),
        ("北京旅游", "rrf"),
    ]
    
    for query, mode in test_cases:
        print(f"\n【查询: '{query}' | 模式: {mode}】")
        
        request = MockRequest({
            "query": query,
            "user_id": "user_001",
            "top_k": 3,
            "data_source": "memcell",
            "retrieval_mode": mode,
        })
        
        try:
            response = await controller.retrieve_lightweight(request)
            result = response.get("result", {})
            memories = result.get("memories", [])
            metadata = result.get("metadata", {})
            
            status = "✅" if len(memories) > 0 else "⚠️"
            print(f"{status} 结果: {len(memories)} 条, 耗时: {metadata.get('total_latency_ms', 0):.2f}ms")
            
            for i, mem in enumerate(memories, 1):
                score = mem.get('score', 0)
                episode = mem.get('episode', '')
                event_id = mem.get('event_id', '')
                print(f"  [{i}] 分数: {score:.4f}")
                print(f"      event_id: {event_id}")
                print(f"      内容: {episode[:100]}...")
            
        except Exception as e:
            print(f"❌ 检索失败: {e}")


async def test_eventlog_retrieval():
    """测试 Event Log 检索（英文查询）"""
    print("\n" + "=" * 100)
    print("🔍 测试 Event Log 检索（英文查询）")
    print("=" * 100)
    
    repository = get_bean_by_type(ConversationMetaRawRepository)
    controller = AgenticV3Controller(repository)
    
    test_cases = [
        ("Beijing travel recommendations", "embedding"),
        ("Forbidden City and Temple of Heaven", "bm25"),
        ("tourist attractions food", "rrf"),
    ]
    
    for query, mode in test_cases:
        print(f"\n【Query: '{query}' | Mode: {mode}】")
        
        request = MockRequest({
            "query": query,
            "user_id": "user_001",
            "top_k": 3,
            "data_source": "event_log",
            "retrieval_mode": mode,
        })
        
        try:
            response = await controller.retrieve_lightweight(request)
            result = response.get("result", {})
            memories = result.get("memories", [])
            metadata = result.get("metadata", {})
            
            status = "✅" if len(memories) > 0 else "⚠️"
            print(f"{status} Results: {len(memories)} items, Latency: {metadata.get('total_latency_ms', 0):.2f}ms")
            
            for i, mem in enumerate(memories, 1):
                score = mem.get('score', 0)
                episode = mem.get('episode', '')
                event_id = mem.get('event_id', '')
                print(f"  [{i}] Score: {score:.4f}")
                print(f"      event_id: {event_id}")
                print(f"      Content: {episode[:100]}...")
            
        except Exception as e:
            print(f"❌ Retrieval failed: {e}")


async def test_semantic_memory_retrieval():
    """测试 Semantic Memory 检索（中文查询）"""
    print("\n" + "=" * 100)
    print("🔍 测试 Semantic Memory 检索（中文查询）")
    print("=" * 100)
    
    repository = get_bean_by_type(ConversationMetaRawRepository)
    controller = AgenticV3Controller(repository)
    
    test_cases = [
        ("美食推荐", "embedding"),
        ("美食推荐", "bm25"),
        ("美食推荐", "rrf"),
    ]
    
    for query, mode in test_cases:
        print(f"\n【查询: '{query}' | 模式: {mode}】")
        
        request = MockRequest({
            "query": query,
            "user_id": "user_001",
            "top_k": 3,
            "data_source": "semantic_memory",
            "retrieval_mode": mode,
        })
        
        try:
            response = await controller.retrieve_lightweight(request)
            result = response.get("result", {})
            memories = result.get("memories", [])
            metadata = result.get("metadata", {})
            
            status = "✅" if len(memories) > 0 else "⚠️"
            print(f"{status} 结果: {len(memories)} 条, 耗时: {metadata.get('total_latency_ms', 0):.2f}ms")
            
            for i, mem in enumerate(memories, 1):
                score = mem.get('score', 0)
                episode = mem.get('episode', '')
                event_id = mem.get('event_id', '')
                memory_type = mem.get('memory_sub_type', '')
                print(f"  [{i}] 分数: {score:.4f}")
                print(f"      event_id: {event_id}")
                print(f"      类型: {memory_type}")
                print(f"      内容: {episode[:100]}...")
            
        except Exception as e:
            print(f"❌ 检索失败: {e}")


async def test_user_filtering():
    """测试用户过滤"""
    print("\n" + "=" * 100)
    print("👤 测试用户过滤")
    print("=" * 100)
    
    repository = get_bean_by_type(ConversationMetaRawRepository)
    controller = AgenticV3Controller(repository)
    
    users = ["user_001", "robot_001"]
    
    for user_id in users:
        print(f"\n【用户: {user_id}】")
        
        request = MockRequest({
            "query": "北京",
            "user_id": user_id,
            "top_k": 3,
            "data_source": "semantic_memory",
            "retrieval_mode": "bm25",
        })
        
        try:
            response = await controller.retrieve_lightweight(request)
            result = response.get("result", {})
            memories = result.get("memories", [])
            
            status = "✅" if len(memories) > 0 else "⚠️"
            print(f"{status} 结果: {len(memories)} 条")
            
            # 验证用户ID
            user_ids = set()
            for mem in memories:
                mem_user_id = mem.get('user_id', '')
                user_ids.add(mem_user_id)
            
            if user_ids:
                print(f"   返回的用户ID: {', '.join(user_ids)}")
                if user_id in user_ids:
                    print(f"   ✓ 包含目标用户 {user_id}")
                else:
                    print(f"   ⚠️  不包含目标用户 {user_id}")
            
        except Exception as e:
            print(f"❌ 检索失败: {e}")


async def test_all_modes_comprehensive():
    """综合测试：所有数据源 × 所有模式"""
    print("\n" + "=" * 100)
    print("🎯 综合测试：所有数据源 × 所有模式")
    print("=" * 100)
    
    repository = get_bean_by_type(ConversationMetaRawRepository)
    controller = AgenticV3Controller(repository)
    
    test_matrix = [
        # (数据源, 查询, 模式, 描述)
        ("memcell", "北京旅游", "embedding", "Episode-向量"),
        ("memcell", "北京旅游", "bm25", "Episode-关键词"),
        ("memcell", "北京旅游", "rrf", "Episode-混合"),
        ("event_log", "travel Beijing food", "embedding", "EventLog-向量"),
        ("event_log", "travel Beijing food", "bm25", "EventLog-关键词"),
        ("event_log", "travel Beijing food", "rrf", "EventLog-混合"),
        ("semantic_memory", "饮食偏好", "embedding", "语义-向量"),
        ("semantic_memory", "饮食偏好", "bm25", "语义-关键词"),
        ("semantic_memory", "饮食偏好", "rrf", "语义-混合"),
    ]
    
    results = []
    
    for data_source, query, mode, desc in test_matrix:
        request = MockRequest({
            "query": query,
            "user_id": "user_001",
            "top_k": 3,
            "data_source": data_source,
            "retrieval_mode": mode,
        })
        
        try:
            response = await controller.retrieve_lightweight(request)
            result = response.get("result", {})
            memories = result.get("memories", [])
            
            success = len(memories) > 0
            results.append((desc, success, len(memories)))
            
        except Exception as e:
            results.append((desc, False, 0))
    
    # 打印结果表格
    print("\n测试结果:")
    print("-" * 60)
    print(f"{'测试项':<20} {'状态':<10} {'结果数':<10}")
    print("-" * 60)
    
    passed = 0
    for desc, success, count in results:
        status = "✅ 通过" if success else "⚠️  失败"
        print(f"{desc:<20} {status:<10} {count:<10}")
        if success:
            passed += 1
    
    print("-" * 60)
    print(f"通过率: {passed}/{len(results)} ({100 * passed // len(results)}%)")
    
    if passed >= len(results) * 0.8:  # 80% 通过即为成功
        print("\n🎉 综合测试通过！")
    else:
        print("\n⚠️  部分测试未通过，请检查。")


async def test_memory_scope_separation():
    """测试 memory_scope：验证个人和群组记忆分离（所有模式）"""
    print("\n" + "=" * 100)
    print("🔍 测试 Memory Scope：个人 vs 群组记忆分离 (所有模式)")
    print("=" * 100)
    
    repository = get_bean_by_type(ConversationMetaRawRepository)
    controller = AgenticV3Controller(repository)
    
    # Episode 和 Semantic 使用中文，EventLog 使用英文
    queries = {
        "episode": "北京旅游",
        "eventlog": "Beijing travel recommendations",
        "semantic": "美食推荐"
    }
    
    # 测试三种数据源 × 三种 scope × 三种模式
    test_matrix = [
        # (数据源, scope, 模式, 描述)
        # Episode 测试
        ("memcell", "all", "embedding", "Episode-All-向量"),
        ("memcell", "all", "bm25", "Episode-All-关键词"),
        ("memcell", "all", "rrf", "Episode-All-混合"),
        ("memcell", "personal", "embedding", "Episode-个人-向量"),
        ("memcell", "personal", "bm25", "Episode-个人-关键词"),
        ("memcell", "personal", "rrf", "Episode-个人-混合"),
        ("memcell", "group", "embedding", "Episode-群组-向量"),
        ("memcell", "group", "bm25", "Episode-群组-关键词"),
        ("memcell", "group", "rrf", "Episode-群组-混合"),
        
        # EventLog 测试
        ("event_log", "all", "embedding", "EventLog-All-向量"),
        ("event_log", "all", "bm25", "EventLog-All-关键词"),
        ("event_log", "all", "rrf", "EventLog-All-混合"),
        ("event_log", "personal", "embedding", "EventLog-个人-向量"),
        ("event_log", "personal", "bm25", "EventLog-个人-关键词"),
        ("event_log", "personal", "rrf", "EventLog-个人-混合"),
        ("event_log", "group", "embedding", "EventLog-群组-向量"),
        ("event_log", "group", "bm25", "EventLog-群组-关键词"),
        ("event_log", "group", "rrf", "EventLog-群组-混合"),
        
        # Semantic Memory 测试
        ("semantic_memory", "all", "embedding", "语义-All-向量"),
        ("semantic_memory", "all", "bm25", "语义-All-关键词"),
        ("semantic_memory", "all", "rrf", "语义-All-混合"),
        ("semantic_memory", "personal", "embedding", "语义-个人-向量"),
        ("semantic_memory", "personal", "bm25", "语义-个人-关键词"),
        ("semantic_memory", "personal", "rrf", "语义-个人-混合"),
        ("semantic_memory", "group", "embedding", "语义-群组-向量"),
        ("semantic_memory", "group", "bm25", "语义-群组-关键词"),
        ("semantic_memory", "group", "rrf", "语义-群组-混合"),
    ]
    
    print(f"\n{'描述':<25} {'模式':<10} {'结果数':<8} {'类型分布'}")
    print("-" * 100)
    
    results_summary = []
    
    for data_source, memory_scope, mode, desc in test_matrix:
        # 根据数据源选择查询语言
        if "EventLog" in desc:
            query = queries["eventlog"]
        elif "语义" in desc:
            query = queries["semantic"]
        else:
            query = queries["episode"]
        
        request = MockRequest({
            "query": query,
            "user_id": "user_001",
            "top_k": 3,
            "data_source": data_source,
            "retrieval_mode": mode,
            "memory_scope": memory_scope,
        })
        
        try:
            response = await controller.retrieve_lightweight(request)
            result = response.get("result", {})
            memories = result.get("memories", [])
            
            # 统计类型
            types = {}
            for mem in memories:
                mem_type = mem.get('memory_sub_type', 'unknown')
                types[mem_type] = types.get(mem_type, 0) + 1
            
            type_str = ", ".join([f"{k}: {v}" for k, v in types.items()]) if types else "无"
            
            status = "✅" if len(memories) > 0 else "⚠️"
            print(f"{status} {desc:<23} {mode:<10} {len(memories):<8} {type_str}")
            
            results_summary.append((desc, mode, len(memories) > 0))
        
        except Exception as e:
            print(f"❌ {desc:<23} {mode:<10} {'错误':<8} {str(e)[:40]}")
            results_summary.append((desc, mode, False))
    
    # 统计通过率
    print("\n" + "=" * 100)
    passed = sum(1 for _, _, success in results_summary if success)
    total = len(results_summary)
    print(f"📊 测试通过率: {passed}/{total} ({100 * passed // total}%)")
    
    if passed == total:
        print("🎉 所有测试通过！")
    else:
        print(f"⚠️  {total - passed} 个测试未通过")


async def main():
    """主函数"""
    print("\n" + "🚀" * 50)
    print("V3 API 记忆检索测试")
    print("🚀" * 50)
    
    start_time = datetime.now()
    
    # 1. Episode 检索（中文）
    await test_episode_retrieval()
    
    # 2. Event Log 检索（英文）
    await test_eventlog_retrieval()
    
    # 3. Semantic Memory 检索（中文）
    await test_semantic_memory_retrieval()
    
    # 4. 用户过滤
    await test_user_filtering()
    
    # 5. 综合测试
    await test_all_modes_comprehensive()
    
    # 6. Memory Scope 测试
    await test_memory_scope_separation()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 100)
    print("✅ 记忆检索测试完成！")
    print(f"⏱️  总耗时: {duration:.2f} 秒")
    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())



async def test_memory_scope_separation():
    """测试 memory_scope：验证个人和群组记忆分离"""
    print("\n" + "=" * 100)
    print("🔍 测试 Memory Scope：个人 vs 群组记忆分离")
    print("=" * 100)
    
    repository = get_bean_by_type(ConversationMetaRawRepository)
    controller = AgenticV3Controller(repository)
    
    query = "北京旅游"
    
    # 测试三种数据源 × 三种 scope
    test_matrix = [
        ("memcell", "all", "所有Episode"),
        ("memcell", "personal", "仅个人Episode"),
        ("memcell", "group", "仅群组Episode"),
        ("event_log", "all", "所有EventLog"),
        ("event_log", "personal", "仅个人EventLog"),
        ("event_log", "group", "仅群组EventLog"),
        ("semantic_memory", "all", "所有语义记忆"),
        ("semantic_memory", "personal", "仅个人语义记忆"),
        ("semantic_memory", "group", "仅群组语义记忆"),
    ]
    
    print(f"\n{'数据源':<20} {'范围':<10} {'描述':<20} {'结果数':<8} {'类型分布'}")
    print("-" * 100)
    
    for data_source, memory_scope, desc in test_matrix:
        request = MockRequest({
            "query": query,
            "user_id": "user_001",
            "top_k": 3,
            "data_source": data_source,
            "retrieval_mode": "rrf",
            "memory_scope": memory_scope,
        })
        
        try:
            response = await controller.retrieve_lightweight(request)
            result = response.get("result", {})
            memories = result.get("memories", [])
            
            # 统计类型
            types = {}
            for mem in memories:
                mem_type = mem.get('memory_sub_type', 'unknown')
                types[mem_type] = types.get(mem_type, 0) + 1
            
            type_str = ", ".join([f"{k}: {v}" for k, v in types.items()]) if types else "无"
            
            print(f"{data_source:<20} {memory_scope:<10} {desc:<20} {len(memories):<8} {type_str}")
        
        except Exception as e:
            print(f"{data_source:<20} {memory_scope:<10} {desc:<20} {'错误':<8} {str(e)[:40]}")
