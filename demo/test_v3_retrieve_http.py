"""V3 API HTTP 记忆检索测试

通过HTTP接口测试V3 API的所有检索功能：
1. Episode 检索（中文查询）
2. Event Log 检索（英文查询）
3. Semantic Memory 检索（中文查询）
4. 用户过滤测试
5. Memory Scope 测试（个人/群组）
"""
import asyncio
import httpx
from typing import Dict, List, Any


# V3 API 基础URL
BASE_URL = "http://localhost:8001"
RETRIEVE_URL = f"{BASE_URL}/api/v3/agentic/retrieve_lightweight"


async def call_retrieve_api(
    query: str,
    user_id: str = "user_001",
    top_k: int = 3,
    data_source: str = "memcell",
    retrieval_mode: str = "embedding",
    memory_scope: str = "all",
) -> Dict[str, Any]:
    """调用V3 API的检索接口"""
    payload = {
        "query": query,
        "user_id": user_id,
        "top_k": top_k,
        "data_source": data_source,
        "retrieval_mode": retrieval_mode,
        "memory_scope": memory_scope,
    }
    
    try:
        # 使用verify=False来跳过SSL证书验证（仅用于本地开发环境）
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            response = await client.post(RETRIEVE_URL, json=payload)
            response.raise_for_status()  # 检查HTTP状态码
            return response.json()
    except httpx.HTTPStatusError as e:
        # HTTP错误（4xx, 5xx）
        return {
            "status": "error",
            "message": f"HTTP {e.response.status_code}: {e.response.text}",
            "error_type": "HTTPStatusError"
        }
    except Exception as e:
        # 其他错误
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }


def print_results(query: str, mode: str, response: Dict[str, Any], scope: str = "all"):
    """打印检索结果"""
    if response.get("status") == "ok":
        result = response.get("result", {})
        memories = result.get("memories", [])
        metadata = result.get("metadata", {})
        
        status = "✅" if len(memories) > 0 else "⚠️"
        scope_text = f" [{scope}]" if scope != "all" else ""
        print(f"{status} '{query}' ({mode}){scope_text}: {len(memories)} 条, "
              f"耗时: {metadata.get('total_latency_ms', 0):.2f}ms")
        
        for i, mem in enumerate(memories[:3], 1):  # 只显示前3条
            score = mem.get('score', 0)
            content = (mem.get('episode') or mem.get('content') or 
                      mem.get('atomic_fact', ''))[:80]
            event_id = mem.get('event_id', 'N/A')
            print(f"  [{i}] 分数: {score:.4f} | event_id: {event_id}")
            print(f"      {content}...")
    else:
        error_msg = response.get("message", "未知错误")
        error_type = response.get("error_type", "")
        # 打印完整的错误信息
        if error_type:
            print(f"❌ '{query}' ({mode}): [{error_type}] {error_msg}")
        else:
            print(f"❌ '{query}' ({mode}): {error_msg}")
        
        # 如果有详细信息，也打印出来
        if "detail" in response:
            print(f"   详细: {response['detail']}")
        elif response.get("status") == "error" and "error_type" not in ["ConnectError"]:
            # 对于非连接错误，显示完整响应
            print(f"   完整响应: {response}")


async def test_episode_retrieval():
    """测试 Episode 检索（中文查询）"""
    print("\n" + "=" * 100)
    print("🔍 测试1: Episode 检索（中文查询）")
    print("=" * 100)
    
    test_cases = [
        ("北京旅游", "embedding"),
        ("北京旅游", "bm25"),
        ("北京旅游", "rrf"),
    ]
    
    for query, mode in test_cases:
        print(f"\n【查询: '{query}' | 模式: {mode}】")
        try:
            response = await call_retrieve_api(
                query=query,
                data_source="memcell",
                retrieval_mode=mode,
            )
            print_results(query, mode, response)
        except httpx.ConnectError:
            print(f"❌ 连接失败: 无法连接到 {BASE_URL}")
            print(f"   请确保 V3 API 服务已启动: uv run python src/bootstrap.py start_server.py")
            return False
        except Exception as e:
            print(f"❌ 检索失败: {e}")
    
    return True


async def test_eventlog_retrieval():
    """测试 Event Log 检索（英文查询）"""
    print("\n" + "=" * 100)
    print("🔍 测试2: Event Log 检索（英文查询）")
    print("=" * 100)
    
    test_cases = [
        ("Beijing travel recommendations", "embedding"),
        ("Forbidden City and Temple of Heaven", "bm25"),
        ("tourist attractions food", "rrf"),
    ]
    
    for query, mode in test_cases:
        print(f"\n【Query: '{query}' | Mode: {mode}】")
        try:
            response = await call_retrieve_api(
                query=query,
                data_source="event_log",
                retrieval_mode=mode,
            )
            print_results(query, mode, response)
        except Exception as e:
            print(f"❌ 检索失败: {e}")


async def test_semantic_memory_retrieval():
    """测试 Semantic Memory 检索（中文查询）"""
    print("\n" + "=" * 100)
    print("🔍 测试3: Semantic Memory 检索（中文查询）")
    print("=" * 100)
    
    test_cases = [
        ("用户喜好", "embedding"),
        ("用户喜好", "bm25"),
        ("用户喜好", "rrf"),
    ]
    
    for query, mode in test_cases:
        print(f"\n【查询: '{query}' | 模式: {mode}】")
        try:
            response = await call_retrieve_api(
                query=query,
                data_source="semantic_memory",
                retrieval_mode=mode,
            )
            print_results(query, mode, response)
        except Exception as e:
            print(f"❌ 检索失败: {e}")


async def test_user_filtering():
    """测试用户过滤"""
    print("\n" + "=" * 100)
    print("🔍 测试4: 用户过滤（Episode检索）")
    print("=" * 100)
    
    test_cases = [
        ("user_001", "向量"),
        ("robot_001", "向量"),
    ]
    
    for user_id, mode_name in test_cases:
        print(f"\n【用户: {user_id} | 模式: {mode_name}】")
        try:
            response = await call_retrieve_api(
                query="旅游",
                user_id=user_id,
                data_source="memcell",
                retrieval_mode="embedding",
                top_k=5,
            )
            print_results(f"{user_id}的记忆", mode_name, response)
        except Exception as e:
            print(f"❌ 检索失败: {e}")


async def test_memory_scope():
    """测试 Memory Scope（个人/群组）"""
    print("\n" + "=" * 100)
    print("🔍 测试5: Memory Scope 过滤")
    print("=" * 100)
    
    # Episode测试
    print("\n【Episode - 不同Scope】")
    for scope in ["all", "personal", "group"]:
        try:
            response = await call_retrieve_api(
                query="北京",
                data_source="memcell",
                retrieval_mode="embedding",
                memory_scope=scope,
                top_k=3,
            )
            print_results("北京", "向量", response, scope)
        except Exception as e:
            print(f"❌ Episode-{scope} 检索失败: {e}")
    
    # Event Log测试
    print("\n【Event Log - 不同Scope】")
    for scope in ["all", "personal", "group"]:
        try:
            response = await call_retrieve_api(
                query="travel",
                data_source="event_log",
                retrieval_mode="embedding",
                memory_scope=scope,
                top_k=3,
            )
            print_results("travel", "向量", response, scope)
        except Exception as e:
            print(f"❌ EventLog-{scope} 检索失败: {e}")
    
    # Semantic Memory测试
    print("\n【Semantic Memory - 不同Scope】")
    for scope in ["all", "personal", "group"]:
        try:
            response = await call_retrieve_api(
                query="用户",
                data_source="semantic_memory",
                retrieval_mode="embedding",
                memory_scope=scope,
                top_k=3,
            )
            print_results("用户", "向量", response, scope)
        except Exception as e:
            print(f"❌ SemanticMemory-{scope} 检索失败: {e}")


async def test_comprehensive():
    """综合测试：所有数据源 × 所有模式 × 所有Scope"""
    print("\n" + "=" * 100)
    print("🔍 测试6: 综合测试矩阵")
    print("=" * 100)
    
    test_matrix = {
        "memcell": {
            "query": "北京旅游",
            "modes": ["embedding", "bm25", "rrf"],
            "scopes": ["all", "personal", "group"],
        },
        "event_log": {
            "query": "Beijing travel",
            "modes": ["embedding", "bm25", "rrf"],
            "scopes": ["all", "personal", "group"],
        },
        "semantic_memory": {
            "query": "用户喜好",
            "modes": ["embedding", "bm25", "rrf"],
            "scopes": ["all", "personal", "group"],
        },
    }
    
    total_tests = 0
    passed_tests = 0
    
    for data_source, config in test_matrix.items():
        print(f"\n【{data_source.upper()} 数据源】")
        
        for mode in config["modes"]:
            for scope in config["scopes"]:
                total_tests += 1
                test_name = f"{data_source}-{mode}-{scope}"
                
                try:
                    response = await call_retrieve_api(
                        query=config["query"],
                        data_source=data_source,
                        retrieval_mode=mode,
                        memory_scope=scope,
                        top_k=2,
                    )
                    
                    if response.get("status") == "ok":
                        result = response.get("result", {})
                        memories = result.get("memories", [])
                        if len(memories) > 0:
                            passed_tests += 1
                            print(f"  ✅ {test_name}: {len(memories)} 条")
                        else:
                            print(f"  ⚠️  {test_name}: 0 条")
                    else:
                        print(f"  ❌ {test_name}: {response.get('message', '失败')}")
                
                except Exception as e:
                    print(f"  ❌ {test_name}: 异常 - {e}")
    
    print(f"\n📊 综合测试结果: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")


async def main():
    """主测试流程"""
    print("\n" + "=" * 100)
    print("🧪 V3 API HTTP 记忆检索测试")
    print("=" * 100)
    print(f"目标服务: {BASE_URL}")
    print(f"检索接口: {RETRIEVE_URL}")
    print("=" * 100)
    
    # 测试1: Episode检索
    success = await test_episode_retrieval()
    if not success:
        print("\n⚠️  服务未启动，测试终止")
        return
    
    # 测试2: Event Log检索
    await test_eventlog_retrieval()
    
    # 测试3: Semantic Memory检索
    await test_semantic_memory_retrieval()
    
    # 测试4: 用户过滤
    await test_user_filtering()
    
    # 测试5: Memory Scope
    await test_memory_scope()
    
    # 测试6: 综合测试
    await test_comprehensive()
    
    print("\n" + "=" * 100)
    print("✅ 所有测试完成！")
    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())

