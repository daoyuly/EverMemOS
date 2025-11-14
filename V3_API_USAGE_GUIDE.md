# V3 API 使用指南 - 存储和检索记忆

## 🎯 概述

V3 API 提供了简单直接的接口来存储和检索记忆，支持：
- **存储**：单条消息存储
- **检索**：27种检索场景（3种数据源 × 3种记忆范围 × 3种检索模式）

**API 基础地址**: `http://localhost:8001`

---

## 1️⃣ 存储记忆 - `/api/v3/agentic/memorize`

### 📝 功能说明

接收单条消息并自动提取为多种记忆类型：
1. **MemCell (episode)** - 群组记忆（user_id=None）
2. **PersonalSemanticMemory** - 个人语义记忆（user_id=具体用户）
3. **PersonalEventLog** - 个人事件日志（user_id=具体用户）

### 🔧 请求格式

**方法**: `POST`
**URL**: `/api/v3/agentic/memorize`
**Content-Type**: `application/json`

```json
{
  "group_id": "chat_user_001_assistant",
  "group_name": "用户与AI助手对话",
  "message_id": "msg_20250115_001",
  "create_time": "2025-01-15T10:00:00+08:00",
  "sender": "user_001",
  "sender_name": "张三",
  "content": "我最近拔了智齿，医生建议吃软食，请问有什么好的建议吗？",
  "refer_list": []
}
```

### 📋 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `group_id` | string | 可选 | 群组ID，用于标识对话 |
| `group_name` | string | 可选 | 群组名称 |
| `message_id` | string | **必需** | 消息唯一标识 |
| `create_time` | string | **必需** | 消息创建时间（ISO 8601格式） |
| `sender` | string | **必需** | 发送者用户ID |
| `sender_name` | string | 可选 | 发送者名称 |
| `content` | string | **必需** | 消息内容 |
| `refer_list` | array | 可选 | 引用的消息ID列表 |

### ✅ 成功响应

```json
{
  "status": "ok",
  "message": "记忆存储成功，共保存 1 条记忆",
  "result": {
    "saved_memories": [
      {
        "memory_type": "episode_summary",
        "user_id": "user_001",
        "group_id": "chat_user_001_assistant",
        "timestamp": "2025-01-15T10:00:00",
        "content": "用户询问拔牙后的饮食建议"
      }
    ],
    "count": 1
  }
}
```

### 🔄 存储流程

```
单条消息
    ↓
1. 提取 MemCell
   - episode: 对话内容摘要
   - semantic_memories: 语义关联（如果启用）
   - event_log: 事件日志（如果启用）
   - user_id: None（群组记忆）
    ↓
2. 保存到 MongoDB
   - memcells 集合
    ↓
3. 同步到 Milvus + ES
   - MemCellSyncService
   - EpisodicMemoryCollection
    ↓
4. 提取个人记忆（如果配置）
   - PersonalSemanticMemory
   - PersonalEventLog
   - user_id: 具体用户
    ↓
5. 保存到 MongoDB
   - personal_semantic_memories 集合
   - personal_event_logs 集合
    ↓
6. 同步到 Milvus + ES
   - PersonalMemorySyncService
   - SemanticMemoryCollection
   - EventLogCollection
```

### 💡 使用示例

#### Python 示例

```python
import requests

url = "http://localhost:8001/api/v3/agentic/memorize"

message = {
    "group_id": "chat_user_001_assistant",
    "group_name": "用户与AI助手对话",
    "message_id": "msg_001",
    "create_time": "2025-01-15T10:00:00+08:00",
    "sender": "user_001",
    "sender_name": "张三",
    "content": "我昨天去北京出差，吃了烤鸭，味道很不错！",
    "refer_list": []
}

response = requests.post(url, json=message)
print(response.json())
```

#### cURL 示例

```bash
curl -X POST http://localhost:8001/api/v3/agentic/memorize \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": "chat_user_001_assistant",
    "message_id": "msg_001",
    "create_time": "2025-01-15T10:00:00+08:00",
    "sender": "user_001",
    "content": "我昨天去北京出差，吃了烤鸭，味道很不错！"
  }'
```

---

## 2️⃣ 检索记忆 - `/api/v3/agentic/retrieve_lightweight`

### 📝 功能说明

支持 **27 种检索场景**，灵活组合：
- **3种数据源**: episode / semantic_memory / event_log
- **3种记忆范围**: all / personal / group
- **3种检索模式**: embedding / bm25 / rrf

### 🔧 请求格式

**方法**: `POST`
**URL**: `/api/v3/agentic/retrieve_lightweight`
**Content-Type**: `application/json`

```json
{
  "query": "北京旅游美食",
  "user_id": "user_001",
  "group_id": "chat_user_001_assistant",
  "time_range_days": 365,
  "top_k": 10,
  "retrieval_mode": "rrf",
  "data_source": "semantic_memory",
  "memory_scope": "personal",
  "current_time": "2025-01-15"
}
```

### 📋 字段说明

| 字段 | 类型 | 必需 | 说明 | 默认值 |
|------|------|------|------|--------|
| `query` | string | **必需** | 查询文本 | - |
| `user_id` | string | 可选 | 用户ID（用于过滤） | null |
| `group_id` | string | 可选 | 群组ID（用于过滤） | null |
| `time_range_days` | int | 可选 | 时间范围（天） | 365 |
| `top_k` | int | 可选 | 返回结果数量 | 20 |
| `retrieval_mode` | string | 可选 | 检索模式 | "rrf" |
| `data_source` | string | 可选 | 数据源 | "memcell" |
| `memory_scope` | string | 可选 | 记忆范围 | "all" |
| `current_time` | string | 可选 | 当前时间（YYYY-MM-DD） | null |

### 🎛️ 参数详解

#### 1. `retrieval_mode` - 检索模式

| 值 | 说明 | 适用场景 |
|----|------|----------|
| `"rrf"` | RRF 融合（默认） | 综合语义和关键词，最推荐 |
| `"embedding"` | 纯向量检索 | 语义相似查询 |
| `"bm25"` | 纯关键词检索 | 精确关键词匹配 |

#### 2. `data_source` - 数据源

| 值 | 说明 | 存储的内容 | user_id |
|----|------|------------|---------|
| `"memcell"` | MemCell.episode（默认） | 对话内容摘要 | None（群组） |
| `"semantic_memory"` | 语义记忆 | 深层语义关联、预测 | 具体用户（个人） |
| `"event_log"` | 事件日志 | 原子事实 | 具体用户（个人） |

#### 3. `memory_scope` - 记忆范围

| 值 | 说明 | 传递参数 | 示例场景 |
|----|------|----------|----------|
| `"all"` | 所有记忆（默认） | user_id ✅ + group_id ✅ | 查询某个用户在某个群组的记忆 |
| `"personal"` | 仅个人记忆 | user_id ✅ + group_id ❌ | 查询某个用户的所有个人记忆 |
| `"group"` | 仅群组记忆 | user_id ❌ + group_id ✅ | 查询某个群组的所有群组记忆 |

### ✅ 成功响应

```json
{
  "status": "ok",
  "message": "检索成功，找到 5 条记忆",
  "result": {
    "memories": [
      {
        "score": 0.85,
        "event_id": "evt_001",
        "user_id": "user_001",
        "group_id": "chat_user_001_assistant",
        "timestamp": "2025-01-15T10:00:00",
        "subject": "北京旅游",
        "episode": "用户提到去北京出差，品尝了烤鸭",
        "summary": "北京出差体验",
        "evidence": "我昨天去北京出差，吃了烤鸭",
        "metadata": {...}
      }
    ],
    "count": 5,
    "metadata": {
      "retrieval_mode": "rrf",
      "data_source": "semantic_memory",
      "embedding_candidates": 15,
      "bm25_candidates": 12,
      "final_count": 5,
      "total_latency_ms": 123.45
    }
  }
}
```

---

## 3️⃣ 27种检索场景示例

### 场景 1-9: episode（对话摘要）

#### 场景 1: episode + all + rrf
```json
{
  "query": "讨论项目进度",
  "user_id": "user_001",
  "group_id": "chat_user_001_assistant",
  "data_source": "episode",
  "memory_scope": "all",
  "retrieval_mode": "rrf"
}
```
**说明**: 查询特定用户在特定群组的对话记忆（同时使用 user_id 和 group_id 过滤）

#### 场景 4: episode + personal + embedding
```json
{
  "query": "讨论项目进度",
  "user_id": "user_001",
  "data_source": "episode",
  "memory_scope": "personal",
  "retrieval_mode": "embedding"
}
```
**说明**: 查询特定用户的所有对话记忆（只使用 user_id 过滤）

#### 场景 7: episode + group + bm25
```json
{
  "query": "讨论项目进度",
  "group_id": "chat_user_001_assistant",
  "data_source": "episode",
  "memory_scope": "group",
  "retrieval_mode": "bm25"
}
```
**说明**: 查询特定群组的所有对话记忆（只使用 group_id 过滤）

---

### 场景 10-18: semantic_memory（语义记忆）

#### 场景 10: semantic + all + rrf
```json
{
  "query": "用户喜欢吃什么",
  "user_id": "user_001",
  "group_id": "chat_user_001_assistant",
  "data_source": "semantic_memory",
  "memory_scope": "all",
  "retrieval_mode": "rrf",
  "current_time": "2025-01-15"
}
```
**说明**: 查询特定用户在特定群组的语义记忆，过滤有效期内的记忆

#### 场景 13: semantic + personal + embedding
```json
{
  "query": "用户的饮食偏好",
  "user_id": "user_001",
  "data_source": "semantic_memory",
  "memory_scope": "personal",
  "retrieval_mode": "embedding",
  "current_time": "2025-01-15"
}
```
**说明**: 查询特定用户的所有语义记忆（个人偏好、习惯等）

#### 场景 16: semantic + group + bm25
```json
{
  "query": "团队共识",
  "group_id": "chat_user_001_assistant",
  "data_source": "semantic_memory",
  "memory_scope": "group",
  "retrieval_mode": "bm25"
}
```
**说明**: 查询特定群组的所有语义记忆（群组共识、惯例等）

---

### 场景 19-27: event_log（事件日志）

#### 场景 19: event_log + all + rrf
```json
{
  "query": "去北京",
  "user_id": "user_001",
  "group_id": "chat_user_001_assistant",
  "data_source": "event_log",
  "memory_scope": "all",
  "retrieval_mode": "rrf"
}
```
**说明**: 查询特定用户在特定群组的事件日志

#### 场景 22: event_log + personal + embedding
```json
{
  "query": "旅游活动",
  "user_id": "user_001",
  "data_source": "event_log",
  "memory_scope": "personal",
  "retrieval_mode": "embedding"
}
```
**说明**: 查询特定用户的所有事件日志

#### 场景 25: event_log + group + bm25
```json
{
  "query": "会议记录",
  "group_id": "chat_user_001_assistant",
  "data_source": "event_log",
  "memory_scope": "group",
  "retrieval_mode": "bm25"
}
```
**说明**: 查询特定群组的所有事件日志

---

## 4️⃣ Python 完整示例

### 存储 + 检索完整流程

```python
import requests
import time

BASE_URL = "http://localhost:8001"

# 1. 存储记忆
def store_memory(message):
    url = f"{BASE_URL}/api/v3/agentic/memorize"
    response = requests.post(url, json=message)
    return response.json()

# 2. 检索记忆
def retrieve_memory(query_params):
    url = f"{BASE_URL}/api/v3/agentic/retrieve_lightweight"
    response = requests.post(url, json=query_params)
    return response.json()

# 示例：存储一条消息
message = {
    "group_id": "chat_user_001_assistant",
    "message_id": f"msg_{int(time.time())}",
    "create_time": "2025-01-15T10:00:00+08:00",
    "sender": "user_001",
    "sender_name": "张三",
    "content": "我昨天去北京出差，吃了烤鸭，味道很不错！还去了故宫参观。"
}

print("存储记忆...")
store_result = store_memory(message)
print(f"存储结果: {store_result['message']}")

# 等待同步完成
time.sleep(2)

# 示例：检索记忆（场景10 - semantic + all + rrf）
print("\n检索记忆...")
query = {
    "query": "北京旅游美食",
    "user_id": "user_001",
    "group_id": "chat_user_001_assistant",
    "data_source": "semantic_memory",
    "memory_scope": "all",
    "retrieval_mode": "rrf",
    "top_k": 5
}

retrieve_result = retrieve_memory(query)
print(f"检索结果: {retrieve_result['message']}")
print(f"找到 {retrieve_result['result']['count']} 条记忆")

for i, mem in enumerate(retrieve_result['result']['memories'], 1):
    print(f"\n记忆 {i}:")
    print(f"  分数: {mem['score']:.2f}")
    print(f"  内容: {mem['episode'][:100]}...")
```

---

## 5️⃣ 最佳实践

### 存储建议

1. **message_id 唯一性**: 确保每条消息的 message_id 唯一
2. **时间格式**: 使用 ISO 8601 格式（`YYYY-MM-DDTHH:mm:ss+08:00`）
3. **批量存储**: 逐条调用 `/memorize` 接口
4. **等待同步**: 存储后等待 1-2 秒再检索，确保同步完成

### 检索建议

1. **选择合适的 data_source**:
   - 对话内容 → `episode`
   - 深层理解 → `semantic_memory`
   - 具体事实 → `event_log`

2. **选择合适的 retrieval_mode**:
   - 一般场景 → `rrf`（推荐）
   - 语义相似 → `embedding`
   - 关键词精确 → `bm25`

3. **选择合适的 memory_scope**:
   - 特定用户+特定群组 → `all`
   - 用户所有记忆 → `personal`
   - 群组所有记忆 → `group`

4. **使用 current_time**: 
   - 检索 `semantic_memory` 时建议传递 `current_time`
   - 自动过滤已过期的语义记忆

---

## 6️⃣ 常见问题

### Q1: 为什么检索不到刚存储的记忆？
**A**: 需要等待 1-2 秒，让系统完成 MongoDB → Milvus/ES 的同步。

### Q2: memory_scope 的 personal 和 group 有什么区别？
**A**: 
- `personal`: 只传递 user_id，查询某个用户的所有记忆
- `group`: 只传递 group_id，查询某个群组的所有记忆
- `all`: 同时传递 user_id 和 group_id，查询某个用户在某个群组的记忆

### Q3: 如何选择 data_source？
**A**:
- `episode`: 适合查询对话内容、讨论主题
- `semantic_memory`: 适合查询深层理解、用户偏好、习惯
- `event_log`: 适合查询具体事件、原子事实

### Q4: RRF 是什么？
**A**: Reciprocal Rank Fusion，融合向量检索和关键词检索的结果，综合语义和精确匹配的优势。

---

## 7️⃣ 完整测试脚本

```bash
# 启动服务
uv run python src/bootstrap.py start_server.py

# 在另一个终端运行测试
uv run python src/bootstrap.py demo/test_retrieval_comprehensive.py
```

这将测试所有 27 种检索场景！

