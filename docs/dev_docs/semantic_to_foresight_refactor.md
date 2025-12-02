# Semantic Memory → Foresight 重命名重构文档

> **重构日期**: 2025-11-25  
> **重构分支**: `origin/refactor/memory-layer-queue`  
> **重构模式**: Big-Bang（一次性全量替换，不保留向后兼容）

---

## 一、重构背景

将项目中所有 "semantic memory"（语义记忆）相关的命名统一更改为 "foresight"（前瞻），包括：
- 文件名
- 类名、枚举值
- 变量名、函数名
- 存储层集合/索引名称
- API 参数值
- 中文注释（语义记忆 → 前瞻）

---

## 二、核心命名变更对照表

| 原名称 | 新名称 | 中文 |
|-------|-------|-----|
| `SEMANTIC_MEMORY` | `FORESIGHT` | 前瞻 |
| `PERSONAL_SEMANTIC_MEMORY` | `PERSONAL_FORESIGHT` | 个人前瞻 |
| `SemanticMemoryModel` | `ForesightModel` | 前瞻模型 |
| `SemanticMemory` | `Foresight` | 前瞻 |
| `SemanticMemoryItem` | `ForesightItem` | 前瞻项目 |
| `semantic_memories` | `foresight_memories` | - |
| `语义记忆` | `前瞻` | - |

---

## 三、文件变更清单

### 3.1 文件重命名 (13个)

| 原路径 | 新路径 |
|-------|-------|
| `src/infra_layer/.../persistence/document/memory/semantic_memory.py` | `foresight.py` |
| `src/infra_layer/.../persistence/document/memory/semantic_memory_record.py` | `foresight_record.py` |
| `src/infra_layer/.../persistence/repository/semantic_memory_raw_repository.py` | `foresight_raw_repository.py` |
| `src/infra_layer/.../persistence/repository/semantic_memory_record_repository.py` | `foresight_record_repository.py` |
| `src/infra_layer/.../search/elasticsearch/memory/semantic_memory.py` | `foresight.py` |
| `src/infra_layer/.../search/elasticsearch/converter/semantic_memory_converter.py` | `foresight_converter.py` |
| `src/infra_layer/.../search/milvus/memory/semantic_memory_collection.py` | `foresight_collection.py` |
| `src/infra_layer/.../search/milvus/converter/semantic_memory_milvus_converter.py` | `foresight_milvus_converter.py` |
| `src/infra_layer/.../search/repository/semantic_memory_es_repository.py` | `foresight_es_repository.py` |
| `src/infra_layer/.../search/repository/semantic_memory_milvus_repository.py` | `foresight_milvus_repository.py` |
| `src/memory_layer/memory_extractor/semantic_memory_extractor.py` | `foresight_extractor.py` |
| `src/memory_layer/prompts/en/semantic_mem_prompts.py` | `foresight_prompts.py` |
| `src/memory_layer/prompts/zh/semantic_mem_prompts.py` | `foresight_prompts.py` |

### 3.2 存储层变更

| 存储类型 | 原名称 | 新名称 |
|---------|-------|-------|
| MongoDB 集合 | `semantic_memories` | `foresights` |
| MongoDB 集合 | `semantic_memory_records` | `foresight_records` |
| Milvus 集合 | `semantic_memory` | `foresight` |
| Elasticsearch 索引 | `semantic-memory` | `foresight` |

### 3.3 API 变更

| 参数 | 原值 | 新值 |
|-----|-----|-----|
| `data_source` | `semantic_memory` | `foresight` |
| `memory_type` | `semantic_memory` | `foresight` |

---

## 四、关键类/函数变更

### 4.1 MemoryType 枚举

```python
# src/agentic_layer/memory_models.py
# 原
MemoryType.SEMANTIC_MEMORY = "semantic_memory"
MemoryType.PERSONAL_SEMANTIC_MEMORY = "personal_semantic_memory"

# 新
MemoryType.FORESIGHT = "foresight"
MemoryType.PERSONAL_FORESIGHT = "personal_foresight"
```

### 4.2 数据模型

```python
# src/agentic_layer/memory_models.py
SemanticMemoryModel  →  ForesightModel

# src/memory_layer/types.py
SemanticMemory       →  Foresight
SemanticMemoryItem   →  ForesightItem
MemCell.semantic_memories  →  MemCell.foresight_memories
Memory.semantic_memories   →  Memory.foresight_memories
```

### 4.3 提取器

```python
# src/memory_layer/memory_extractor/foresight_extractor.py
SemanticMemoryExtractor  →  ForesightExtractor
generate_semantic_memories_for_memcell  →  generate_foresight_memories_for_memcell
generate_semantic_memories_for_episode  →  generate_foresight_memories_for_episode
```

### 4.4 仓库层

```python
# 持久化仓库
SemanticMemoryRawRepository        →  ForesightRawRepository
SemanticMemoryRecordRawRepository  →  ForesightRecordRawRepository

# 搜索仓库
SemanticMemoryMilvusRepository  →  ForesightMilvusRepository
SemanticMemoryEsRepository      →  ForesightEsRepository
```

### 4.5 转换器

```python
SemanticMemoryConverter        →  ForesightConverter
SemanticMemoryMilvusConverter  →  ForesightMilvusConverter
```

### 4.6 同步服务

```python
# src/biz_layer/mem_sync.py
sync_batch_semantic_memories  →  sync_batch_foresights
sync_semantic_memory          →  sync_foresight
```

---

## 五、配置变更

### 5.1 Demo 配置

```python
# demo/config/memory_config.py
enable_semantic_extraction  →  enable_foresight_extraction
```

### 5.2 Evaluation 配置

```python
# evaluation/src/adapters/evermemos/config.py
enable_semantic_extraction  →  enable_foresight_extraction
```

---

## 六、修改统计

| 统计项 | 数量 |
|-------|-----|
| 修改文件总数 | 52 |
| 文件重命名 | 13 |
| 新增行数 | +817 |
| 删除行数 | -816 |
| Linter 错误 | 0 |

---

## 七、测试注意事项

### 7.1 数据库清理

由于采用 Big-Bang 模式，需要清理旧的存储数据：

```bash
# MongoDB - 删除或重建以下集合:
db.semantic_memories.drop()
db.semantic_memory_records.drop()

# Milvus - 删除或重建以下集合:
# 集合名: semantic_memory

# Elasticsearch - 删除或重建以下索引:
# 索引名: semantic-memory
```

### 7.2 API 测试检查点

```python
# 检索 API 请求参数
{
    "data_source": "foresight",  # 原 "semantic_memory"
    ...
}

# 返回的 memory_type
MemoryType.FORESIGHT  # 原 MemoryType.SEMANTIC_MEMORY
```

### 7.3 验证命令

```bash
# 1. 确认无遗漏的旧名称
grep -r "semantic_memory\|SemanticMemory\|SEMANTIC_MEMORY\|语义记忆" src/

# 2. Python 语法检查
python -m py_compile src/biz_layer/mem_sync.py \
    src/biz_layer/memorize_worker_service.py \
    src/agentic_layer/memory_manager.py

# 3. 查看变更文件
git diff --stat HEAD

# 4. 运行单元测试
pytest tests/test_memory_models.py -v
pytest tests/test_fetch_mem_service.py -v
```

---

## 八、回滚说明

如需回滚，可通过 Git 恢复：

```bash
git checkout HEAD~1 -- .
# 或
git revert <commit-hash>
```

---

## 九、相关文档

- [Agentic V3 API 文档 (中文)](../api_docs/agentic_v3_api_zh.md)
- [Agentic V3 API 文档 (英文)](../api_docs/agentic_v3_api.md)

