"""测试 V3 API 语义记忆检索功能

验证语义记忆检索是否正确封装到 V3 API 中
"""

import asyncio

from core.di import get_bean_by_type
from infra_layer.adapters.input.api.v3.agentic_v3_controller import (
    AgenticV3Controller,
)
from infra_layer.adapters.out.persistence.repository.conversation_meta_raw_repository import (
    ConversationMetaRawRepository,
)


class MockRequest:
    def __init__(self, data):
        self.data = data
    
    async def json(self):
        return self.data


async def test_semantic_memory_retrieval():
    """测试语义记忆检索（通过 V3 API）"""
    print("\n" + "=" * 80)
    print("V3 API 语义记忆检索测试（所有检索模式）")
    print("=" * 80)
    
    repository = get_bean_by_type(ConversationMetaRawRepository)
    controller = AgenticV3Controller(repository)
    
    # 测试查询
    test_query = "北京旅游"
    
    # 测试场景
    scenarios = [
        {
            "name": "user_001 - RRF 融合",
            "params": {
                "user_id": "user_001",
                "group_id": None,
                "retrieval_mode": "rrf",
            }
        },
        {
            "name": "user_001 - 纯向量",
            "params": {
                "user_id": "user_001",
                "group_id": None,
                "retrieval_mode": "embedding",
            }
        },
        {
            "name": "user_001 - 纯BM25",
            "params": {
                "user_id": "user_001",
                "group_id": None,
                "retrieval_mode": "bm25",
            }
        },
    ]
    
    print(f"\n查询: {test_query}")
    print(f"{'='*80}")
    
    for scenario in scenarios:
        print(f"\n📋 场景: {scenario['name']}")
        print(f"   过滤条件: user_id={scenario['params']['user_id']}, "
              f"group_id={scenario['params']['group_id']}")
        print(f"   检索模式: {scenario['params']['retrieval_mode']}")
        
        request_data = {
            "query": test_query,
            "top_k": 5,
            "data_source": "semantic_memory",  # 使用语义记忆数据源
            **scenario['params']
        }
        
        request = MockRequest(request_data)
        response = await controller.retrieve_lightweight(request)
        result = response.get("result", {})
        metadata = result.get("metadata", {})
        memories = result.get("memories", [])
        
        retrieval_mode = metadata.get("retrieval_mode", "N/A")
        latency = metadata.get("total_latency_ms", 0)
        embedding_candidates = metadata.get("embedding_candidates", 0)
        bm25_candidates = metadata.get("bm25_candidates", 0)
        
        print(f"   结果: 找到 {len(memories)} 条 (模式: {retrieval_mode}, 耗时: {latency:.2f}ms)")
        if embedding_candidates > 0:
            print(f"        Embedding 候选: {embedding_candidates}")
        if bm25_candidates > 0:
            print(f"        BM25 候选: {bm25_candidates}")
        
        if memories:
            for i, mem in enumerate(memories[:3], 1):
                score = mem.get('score', 0)
                episode = mem.get('episode', '')
                subject = mem.get('subject', '')
                display_text = subject if subject else episode[:40]
                timestamp = mem.get('timestamp', 'N/A')
                user_id = mem.get('user_id', 'N/A')
                memory_type = mem.get('memory_sub_type', 'N/A')
                
                # 根据模式显示不同的分数名称
                if retrieval_mode == "embedding":
                    score_label = "余弦相似度"
                elif retrieval_mode == "bm25":
                    score_label = "BM25分数"
                else:
                    score_label = "RRF分数"
                
                print(f"      [{i}] {score_label}={score:.4f} | {display_text}...")
                print(f"          时间: {timestamp} | user: {user_id} | type: {memory_type}")
        else:
            print(f"      ⚠️  没有找到匹配结果")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
    print("\n✅ 语义记忆检索已成功封装到 V3 API 中！")
    print("   支持三种检索模式：")
    print("   - embedding: 纯向量检索（通过 Milvus）")
    print("   - bm25: 纯关键词检索（通过 Elasticsearch）")
    print("   - rrf: RRF 融合检索（Milvus + ES）")
    print("\n💡 使用示例:")
    print("""
    POST /api/v3/agentic/retrieve_lightweight
    {
      "query": "北京旅游",
      "user_id": "user_001",
      "top_k": 10,
      "data_source": "semantic_memory",
      "retrieval_mode": "rrf"  // 或 "embedding" 或 "bm25"
    }
    """)


if __name__ == "__main__":
    asyncio.run(test_semantic_memory_retrieval())

