"""V3 API 记忆存储测试

功能：
1. 清空所有数据库数据（MongoDB, Milvus, ES）
2. 从 assistant_chat_zh.json 读取对话数据
3. 调用 V3 API 提取并存储记忆
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from core.di import get_bean_by_type
from infra_layer.adapters.out.persistence.document.memory.memcell import MemCell
from infra_layer.adapters.out.persistence.document.memory.episodic_memory import EpisodicMemory
from infra_layer.adapters.out.persistence.document.memory.personal_semantic_memory import PersonalSemanticMemory
from infra_layer.adapters.out.persistence.document.memory.personal_event_log import PersonalEventLog
from infra_layer.adapters.out.persistence.document.memory.semantic_memory import SemanticMemory
from infra_layer.adapters.out.search.repository.episodic_memory_milvus_repository import EpisodicMemoryMilvusRepository
from infra_layer.adapters.out.search.repository.episodic_memory_es_repository import EpisodicMemoryEsRepository


async def clear_all_data():
    """清空所有数据库数据"""
    print("=" * 100)
    print("🗑️  清空所有数据库数据")
    print("=" * 100)
    
    # 1. 清空 MongoDB
    print("\n【1】清空 MongoDB 集合...")
    
    memcell_count = await MemCell.find_all().count()
    await MemCell.find_all().delete()
    print(f"  ✅ MemCell: 删除 {memcell_count} 条")
    
    episodic_count = await EpisodicMemory.find_all().count()
    await EpisodicMemory.find_all().delete()
    print(f"  ✅ EpisodicMemory: 删除 {episodic_count} 条")
    
    semantic_count = await SemanticMemory.find_all().count()
    await SemanticMemory.find_all().delete()
    print(f"  ✅ SemanticMemory: 删除 {semantic_count} 条")
    
    personal_semantic_count = await PersonalSemanticMemory.find_all().count()
    await PersonalSemanticMemory.find_all().delete()
    print(f"  ✅ PersonalSemanticMemory: 删除 {personal_semantic_count} 条")
    
    personal_eventlog_count = await PersonalEventLog.find_all().count()
    await PersonalEventLog.find_all().delete()
    print(f"  ✅ PersonalEventLog: 删除 {personal_eventlog_count} 条")
    
    # 2. 清空 Milvus
    print("\n【2】清空 Milvus 数据...")
    milvus_repo = get_bean_by_type(EpisodicMemoryMilvusRepository)
    try:
        # 直接删除所有数据（使用 id != "" 匹配所有记录）
        milvus_collection = milvus_repo.collection
        
        # 先查询总数
        total_before = len(await milvus_collection.query(expr='id != ""', output_fields=["id"], limit=16384))
        
        # 删除所有数据
        await milvus_collection.delete(expr='id != ""')
        await milvus_repo.flush()
        print(f"  ✅ Milvus: 删除 {total_before} 条")
    except Exception as e:
        print(f"  ⚠️  Milvus 清空失败: {e}")
    
    # 3. 清空 Elasticsearch
    print("\n【3】清空 Elasticsearch 数据...")
    es_repo = get_bean_by_type(EpisodicMemoryEsRepository)
    try:
        # 删除所有数据（使用 match_all 查询）
        client = await es_repo.get_client()
        index_name = es_repo.get_index_name()
        
        response = await client.delete_by_query(
            index=index_name,
            body={"query": {"match_all": {}}},
            refresh=True
        )
        
        deleted_count = response.get('deleted', 0)
        print(f"  ✅ Elasticsearch: 删除 {deleted_count} 条")
    except Exception as e:
        print(f"  ⚠️  ES 清空失败: {e}")
    
    print("\n✅ 所有数据已清空！\n")


async def load_conversation_data(file_path: str):
    """加载对话数据"""
    print("=" * 100)
    print("📖 加载对话数据")
    print("=" * 100)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取 conversation_list 列表
    messages = data.get('conversation_list', [])
    conversation_meta = data.get('conversation_meta', {})
    
    print(f"\n文件: {file_path}")
    print(f"对话轮数: {len(messages)} 轮")
    print(f"群组ID: {conversation_meta.get('group_id', 'unknown')}")
    
    # 显示前3轮对话
    print("\n前3轮对话预览:")
    for i, msg in enumerate(messages[:3]):
        sender = msg.get('sender', 'unknown')
        content = msg.get('content', '')[:100]
        print(f"  [{i}] {sender}: {content}...")
    
    return data


async def extract_memories(conversation_data: dict):
    """使用 MemoryManager 提取记忆（与 test_v3_api_simple.py 相同方式）"""
    print("\n" + "=" * 100)
    print("🧠 提取记忆（使用 MemoryManager.memorize）")
    print("=" * 100)
    
    # 从数据中提取 conversation_list 和 meta 信息
    raw_messages = conversation_data.get('conversation_list', [])
    conversation_meta = conversation_data.get('conversation_meta', {})
    group_id = conversation_meta.get('group_id', 'test_group_001')
    
    print(f"\n对话消息数: {len(raw_messages)} 条")
    print(f"群组ID: {group_id}")
    
    # 初始化 MemoryManager
    from agentic_layer.memory_manager import MemoryManager
    from memory_layer.types import RawDataType
    from memory_layer.memcell_extractor.base_memcell_extractor import RawData
    from memory_layer.memory_manager import MemorizeRequest
    from common_utils.datetime_utils import from_iso_format
    
    manager = MemoryManager()
    
    # 逐条处理消息
    history = []
    saved_count = 0
    start_time = datetime.now()
    
    print("\n开始提取记忆...")
    
    for idx, msg in enumerate(raw_messages):
        # 构造消息数据
        timestamp_str = msg.get('create_time')
        if not timestamp_str:
            continue
        
        timestamp_dt = from_iso_format(timestamp_str)
        speaker_id = msg.get('sender')
        speaker_name = msg.get('sender_name', speaker_id)
        content = msg.get('content', '')
        message_id = msg.get('message_id', f"msg_{idx}")
        
        message_payload = {
            "speaker_id": speaker_id,
            "speaker_name": speaker_name,
            "content": content,
            "timestamp": timestamp_dt,
        }
        
        raw_item = RawData(
            content=message_payload,
            data_id=str(message_id),
            data_type=RawDataType.CONVERSATION,
        )
        
        # 初始化历史
        if not history:
            history.append(raw_item)
            continue
        
        # 构建请求 - 提取所有参与者
        participants = set()
        for h in history:
            speaker_id = h.content.get("speaker_id")
            if speaker_id:
                participants.add(speaker_id)
        # 添加当前消息的 speaker_id
        if message_payload.get("speaker_id"):
            participants.add(message_payload["speaker_id"])
        
        user_id_list = list(participants) if participants else ["default"]
        
        request = MemorizeRequest(
            history_raw_data_list=list(history),
            new_raw_data_list=[raw_item],
            raw_data_type=RawDataType.CONVERSATION,
            user_id_list=user_id_list,
            group_id=group_id,
            enable_semantic_extraction=True,   # 启用语义记忆
            enable_event_log_extraction=True,  # 启用 Event Log
        )
        
        # 调用 memorize
        result = await manager.memorize(request)
        
        if result:
            saved_count += 1
            print(f"  [{saved_count}] ✅ 提取成功，返回 {len(result)} 个 Memory")
            
            # 重置历史
            history = [raw_item]
        else:
            # 继续累积
            history.append(raw_item)
            if len(history) > 20:
                history = history[-20:]
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n{'='*100}")
    print("📊 提取统计")
    print(f"{'='*100}")
    print(f"  总消息数: {len(raw_messages)} 条")
    print(f"  提取 MemCell 数: {saved_count} 个")
    print(f"  总耗时: {duration:.2f} 秒")
    
    print(f"\n✅ 记忆提取完成！")
    return saved_count


async def verify_storage():
    """验证数据存储"""
    print("\n" + "=" * 100)
    print("✓ 验证数据存储")
    print("=" * 100)
    
    # MongoDB 统计
    print("\n【MongoDB】")
    memcell_count = await MemCell.find_all().count()
    episodic_count = await EpisodicMemory.find_all().count()
    semantic_count = await PersonalSemanticMemory.find_all().count()
    eventlog_count = await PersonalEventLog.find_all().count()
    
    print(f"  MemCell: {memcell_count} 条")
    print(f"  EpisodicMemory (个人情景): {episodic_count} 条")
    print(f"  PersonalSemanticMemory: {semantic_count} 条")
    print(f"  PersonalEventLog: {eventlog_count} 条")
    
    # Milvus 统计
    print("\n【Milvus】")
    milvus_repo = get_bean_by_type(EpisodicMemoryMilvusRepository)
    from agentic_layer.vectorize_service import get_vectorize_service
    
    vectorize_service = get_vectorize_service()
    query_vec = await vectorize_service.get_embedding("测试")
    
    milvus_results = await milvus_repo.vector_search(
        query_vector=query_vec,
        limit=500,
    )
    
    type_stats = {}
    for result in milvus_results:
        memory_type = result.get('memory_sub_type', 'unknown')
        type_stats[memory_type] = type_stats.get(memory_type, 0) + 1
    
    print(f"  总记录数: {len(milvus_results)} 条")
    for memory_type, count in sorted(type_stats.items()):
        print(f"    - {memory_type}: {count} 条")
    
    # Elasticsearch 统计
    print("\n【Elasticsearch】")
    es_repo = get_bean_by_type(EpisodicMemoryEsRepository)
    import jieba
    
    es_hits = await es_repo.multi_search(
        query=list(jieba.cut("测试")),
        size=500,
    )
    
    es_type_stats = {}
    for hit in es_hits:
        source = hit.get('_source', {})
        es_type = source.get('type', 'unknown')
        es_type_stats[es_type] = es_type_stats.get(es_type, 0) + 1
    
    print(f"  总记录数: {len(es_hits)} 条")
    for es_type, count in sorted(es_type_stats.items()):
        print(f"    - {es_type}: {count} 条")
    
    # 判断是否成功
    all_success = (
        memcell_count > 0 and
        len(milvus_results) > 0 and
        len(es_hits) > 0
    )
    
    if all_success:
        print("\n🎉 数据存储验证通过！")
    else:
        print("\n⚠️  数据存储可能有问题，请检查。")
    
    return all_success


async def main():
    """主函数"""
    print("\n" + "🚀" * 50)
    print("V3 API 记忆存储测试")
    print("🚀" * 50)
    
    # 1. 清空数据
    await clear_all_data()
    
    # 2. 加载对话数据
    data_file = "/Users/admin/Documents/Projects/opensource/memsys-opensource/data/assistant_chat_zh.json"
    conversation_data = await load_conversation_data(data_file)
    
    # 3. 提取记忆
    success = await extract_memories(conversation_data)
    
    if not success:
        print("\n❌ 记忆提取失败，退出。")
        return
    
    # 4. 等待同步完成
    print("\n⏳ 等待数据同步完成（3秒）...")
    await asyncio.sleep(3)
    
    # 5. 验证存储
    await verify_storage()
    
    print("\n" + "=" * 100)
    print("✅ 记忆存储测试完成！")
    print("=" * 100)
    print("\n💡 提示: 现在可以运行 v3_retrieve_memories.py 进行检索测试")


if __name__ == "__main__":
    asyncio.run(main())

