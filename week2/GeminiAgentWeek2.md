
# 📘 Google Gemini API 开发者实战手册 (Python 版) - Week 2

**版本：** 1.0 (进阶篇)

**时间：** 2026年1月

**适用对象：** DevOps / 后端工程师 / AI 应用架构师

**核心目标：** 突破模型上下文限制，构建具备“私有知识库”的企业级 RAG (检索增强生成) 系统。

---

## 目录

1.  [Day 7: AI 的翻译官 (Embeddings)](#day-7-ai-的翻译官-embeddings)
2.  [Day 8: 记忆仓库 (Vector DB & ChromaDB)](#day-8-记忆仓库-vector-db--chromadb)
3.  [Day 9: RAG 系统总装 (The Assembly)](#day-9-rag-系统总装-the-assembly)
4.  [Day 10: 进阶切片 (Chunking & Context)](#day-10-进阶切片-chunking--context)

---

## Day 7: AI 的翻译官 (Embeddings)

### 核心概念
* **向量 (Vector)**：将文字转化为一串数字（坐标，如 `[0.1, -0.9, ...]`），让计算机通过计算“空间距离”来理解“语义相似度”。
* **语义搜索 vs 关键字搜索**：
    * **关键字**：搜 "DB" 找不到 "Database"（因为字面不同）。
    * **语义**：搜 "DB" 能找到 "Database"，也能找到 "数据仓库"（因为在语义空间里靠得近）。
* **数学基础**：通常使用 **点积 (Dot Product)** 或 **余弦相似度 (Cosine Similarity)** 来计算距离。

### ⚡️ 避坑指南 (关键考点)
Gemini 的 Embedding 模型对“提问”和“文档”有严格区分，配置错误会导致匹配分数值失效（导致中文文档得分极低）。

### 📝 核心代码片段
```python
import google.generativeai as genai

# ✅ 正确做法：必须区分 task_type

def get_doc_embedding(text):
    """用于知识库文档入库"""
    return genai.embed_content(
        model="models/text-embedding-004", # 或 gemini-embedding-001
        content=text,
        task_type="retrieval_document", # 文档专用
        title="Knowledge Base"          # 文档建议加 Title
    )['embedding']

def get_query_embedding(text):
    """用于用户提问"""
    return genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_query"     # 提问专用
        # ❌ 严禁在此处加 title 参数
    )['embedding']
```

## Day 8: 记忆仓库 (Vector DB & ChromaDB)

### 核心概念
* **为什么需要数据库？**：手动计算 `np.dot` 速度太慢 ($O(N)$)。向量数据库利用 **HNSW** 等索引算法实现海量数据的毫秒级近似搜索 ($O(\log N)$)。
* **ChromaDB**：Python 生态中最轻量、嵌入式的向量数据库，类似“带 AI 脑子的 MongoDB”。
* **Metadata (元数据)**：Embeddings 负责“模糊匹配”，Metadata 负责“精准过滤” (Filtering)。

### 📝 核心代码片段
```python
import chromadb

# 初始化内存模式的客户端
client = chromadb.Client()
collection = client.create_collection("devops_logs")

# 1. 写入数据 (带 Metadata)
# Metadata 是 RAG 系统的“过滤器”和“溯源证据”
collection.add(
    documents=["Redis 响应慢", "午饭很好吃"],
    metadatas=[{"env": "prod", "severity": "high"}, {"env": "life"}],
    ids=["doc1", "doc2"]
)

# 2. 混合查询 (语义 + 过滤)
results = collection.query(
    query_texts=["数据库卡顿"],
    n_results=1,
    where={"env": "prod"} # 🔥 核心：只搜生产环境
)
```

## Day 9: RAG 系统总装 (The Assembly)

### 核心架构
1.  **Retrieve (检索)**：用户提问 -> 变成向量 -> ChromaDB 找回 Top-K 文档。
2.  **Augment (增强)**：将“用户问题”和“找回的文档”拼接到一起，形成新的 Context Prompt。
3.  **Generate (生成)**：LLM 阅读拼接后的 Prompt，生成最终答案。

### 🛡️ 消除幻觉 (Anti-Hallucination)
RAG 的核心在于限制 AI 的发散能力，强制其“开卷考试”。

### 📝 核心代码片段
```python
def ask_jarvis(user_query):
    # 1. Retrieve (检索)
    results = collection.query(query_texts=[user_query], n_results=3)
    context_str = "\n".join(results['documents'][0])
    
    # 2. Augment (增强) & Prompt Engineering
    prompt = f"""
    你是一个运维专家。请 **仅根据** 以下参考资料回答用户问题。
    如果资料中没有答案，请直接说“我不知道”，**不要编造**。

    参考资料：
    {context_str}

    用户问题：{user_query}
    """
    
    # 3. Generate (生成)
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model.generate_content(prompt).text
```

## Day 10: 进阶切片 (Chunking & Context)

### 核心痛点
* **长文档问题**：一本 50 页的手册不能直接转向量（丢失细节、Token 超限）。
* **断章取义**：切片可能把“原因”和“解决方案”切到了不同的块里。

### 解决方案
* **Chunking (切片)**：将长文档切成小块（如 300-500 字符）。
* **Overlap (重叠)**：切片之间保留 10-20% 重叠，防止逻辑断层。
* **Window Retrieval (窗口检索)**：**检索用小切片，生成用大窗口**。

### 📝 核心代码片段 (方案 B: 窗口检索)
```python
# 1. 向量搜索定位核心切片 (Anchor)
results = collection.query(query_texts=[user_query], n_results=1)

# 获取命中切片的 ID (例如 "chunk_5")
anchor_id = results['ids'][0][0] 
# 获取命中切片的 Index (例如 5)
anchor_index = results['metadatas'][0][0]['chunk_index']

# 2. 自动抓取前后文 (Window Expansion)
# 直接用 ID 去库里拿，不走向量搜索，补全逻辑
context_ids = [
    f"chunk_{anchor_index - 1}", # 前文
    f"chunk_{anchor_index}",     # 当前文
    f"chunk_{anchor_index + 1}"  # 后文
]

# 3. 批量获取原文
full_context_docs = collection.get(ids=context_ids)['documents']
full_context = "\n".join(full_context_docs)

# 4. 喂给 AI
# 这样 AI 既能看到 "不要重启数据库"，也能看到下一段的 "应该执行 SQL..."
```