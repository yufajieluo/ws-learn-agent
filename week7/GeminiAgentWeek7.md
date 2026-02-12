# 📘 Google Gemini API 开发者实战手册 (Python 版) - Week 7

**版本：** 1.0 (Agent 架构篇)

**时间：** 2026年2月

**适用对象：** AI 全栈工程师 / 架构师

**核心目标：** 突破模型知识截止限制，构建具备“联网搜索”与“私有知识库查阅”能力的自主 Agent。

---

## 目录

1.  [Day 29: AI 的千里眼 (Web Search & Tools)](#day-29-ai-的千里眼-web-search--tools)
2.  [Day 30: 向量化的奥义 (Vector Store & ChromaDB)](#day-30-向量化的奥义-vector-store--chromadb)
3.  [Day 31: RAG 工具化 (Retriever as a Tool)](#day-31-rag-工具化-retriever-as-a-tool)
4.  [Day 32: 终极融合 (The Super Agent)](#day-32-终极融合-the-super-agent)

---

---
## Day 29: AI 的千里眼 (Web Search & Tools)

### 🎯 核心概念
- **知识截止 (Knowledge Cutoff)**：LLM 的知识只停留在训练结束那天（例如 2024/2025年）。
- **Agent (智能体)**：与 Chatbot 不同，Agent 拥有使用 工具 (Tools) 的能力，可以主动获取外部信息。
- **Tavily Search**：专为 AI 设计的搜索引擎，返回的是结构化的 JSON 摘要，而非一堆杂乱的 HTML 链接。

### 📝 核心代码
```python
from langchain_community.tools.tavily_search import TavilySearchResults

# 1. 初始化搜索工具
tool = TavilySearchResults(
    max_results=3,
    include_answer=True,
    include_raw_content=True
)

# 2. 绑定到 LLM
llm_with_tools = llm.bind_tools([tool])

# 3. AI 自动决策
# 如果问 "今天天气"，AI 会生成 tool_calls；如果问 "你好"，则不会。
response = llm_with_tools.invoke("现在 Nvidia 股价是多少？")
```

---
## Day 30: 向量化的奥义 (Vector Store & ChromaDB)

### 🎯 核心概念
- **Embeddings (嵌入)**：将文本转化为向量坐标（如 `[0.1, -0.9, ...]` ）。语义越近，距离越近。
- **Vector DB (Chroma)**：专门存储这些坐标的数据库，支持毫秒级相似度搜索。
- **Week 2 vs Week 7 的区别**：
    - **Week 2 (Context Stuffing)**：手动把文本塞进 Prompt，费钱、长度有限。
    - **Week 7 (Vector RAG)**：只检索最相关的 Top-K 片段，容量无限，适合大规模知识库。

### 📝 核心代码
```python
# 1. 智能切片 (保留语义完整性)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)

# 2. 写入数据库 (Ingest) - 仅需运行一次
vectorstore = Chroma.from_documents(
    documents=splits,
    embedding=embedding_function, # task_type="retrieval_document"
    persist_directory="./chroma_db_data"
)

# 3. 读取数据库 (Load) - 日常使用
vectorstore = Chroma(
    persist_directory="./chroma_db_data",
    embedding_function=embedding_function # task_type="retrieval_query"
)

# 4. 生成检索器接口
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
```

---

## Day 31: RAG 工具化 (Retriever as a Tool)

### 🎯 核心概念
- **Retriever vs Tool**：
    - **Retriever** 是给代码用的（`invoke()`）。
    - **Tool** 是给 LLM 用的（带 `name` 和 `description`）。
- **语义路由 (Semantic Routing)**：通过编写精准的 `description`，让 AI 自己判断何时查库（例如：“仅在询问 Jarvis 内部配置时使用”）。

---

## Day 32: 终极融合 (The Super Agent)
### 🎯 核心概念
- **多工具分发**：Agent 同时拥有 `search_public_internet` (Tavily) 和 `search_internal_knowledge` (Chroma)。
- **并行调用 (Parallel Function Calling)**：Gemini 2.0 具备在一次思考中同时调用多个工具的能力（例如同时查内网 IP 和外网天气）。
- **LangGraph 工作流**：使用 `StateGraph` 构建循环图，支持 `思考 -> 工具 -> 再思考` 的 ReAct 模式。


### 📝 核心代码
```python
# 1. 组装工具箱
tools = [tool_internal, tool_internet]

# 2. 绑定大脑
llm_with_tools = llm.bind_tools(tools)

# 3. 定义图结构 (LangGraph)
workflow = StateGraph(AgentState)
workflow.add_node("agent", chatbot)       # 思考节点
workflow.add_node("tools", tool_node)     # 执行节点

# 4. 条件边 (Conditional Edge)
# AI 决定：是结束对话 (__end__) 还是去调用工具 (tools)
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")       # 工具用完回传给 AI

app = workflow.compile()
```