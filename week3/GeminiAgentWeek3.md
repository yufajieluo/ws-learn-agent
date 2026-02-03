# 📘 Google Gemini API 开发者实战手册 (Python 版) - Week 3

**版本：** 1.0 (架构篇)

**时间：** 2026年1月

**适用对象：** DevOps / SRE / AI 全栈工程师

**核心目标：** 掌握 LangChain 框架，构建可视化、可交互、具备高级推理能力的 AI 运维助手。

---

## 目录

1.  [Day 11: 工业级流水线 (LangChain Basics)](#day-11-工业级流水线-langchain-basics)
2.  [Day 12: 让 AI 学会思考 (CoT & Reasoning)](#day-12-让-ai-学会思考-cot--reasoning)
3.  [Day 13: 赋予面孔 (Streamlit UI)](#day-13-赋予面孔-streamlit-ui)
4.  [Day 14: 终极实战 (Jarvis-Ops Pro)](#day-14-终极实战-jarvis-ops-pro)

---

## Day 11: 工业级流水线 (LangChain Basics)

### 🎯 核心目标
从手写 Python 胶水代码转向使用 **LCEL (LangChain Expression Language)** 构建标准化的 AI 流水线。

### 💡 关键知识点

#### 1. LCEL (声明式编程)
* **概念**：使用管道符 `|` 将组件串联，像 Linux 管道一样处理数据流。
* **优势**：自动处理并行调用、流式输出和类型转换。
* **公式**：`Chain = Retriever | Prompt | LLM | Parser`

#### 2. RAG 核心组件
* **Retriever (检索器)**：
    * `vectorstore.as_retriever(search_kwargs={'k': 3})`
    * **search_kwargs**：向底层向量库（Chroma）透传配置的万能接口。`k` 控制召回数量（Top-K）。
* **RunnablePassthrough**：
    * 数据流的“透传管道”。在 RAG 中用于将用户的 `question` 直接传给 Prompt，而不进行任何修改。

#### 3. Debug 经验
* **ImportError**：LangChain 0.2+ 进行了模块拆分，文本切割器需从 `langchain_text_splitters` 导入，向量库需从 `langchain_chroma` 导入。
* **Token 消耗**：Chain 的构建过程（定义对象）不消耗 Token，只有执行 `.invoke()` 时才会产生 API 费用。

### 💻 代码片段
```python
# 标准 RAG 链结构
chain = (
    # 并行处理：同时去查文档(context) 和 透传问题(question)
    {"context": retriever, "question": RunnablePassthrough()} 
    | prompt 
    | llm 
    | StrOutputParser()
)
```


## Day 12: 让 AI 学会思考 (CoT & Reasoning)

### 🎯 核心目标
从“直觉式回答” (System 1) 进化为“逻辑推理” (System 2)，让 AI 学会像 SRE 专家一样排查问题。

### 💡 关键知识点

#### 1. Zero-Shot vs Few-Shot
* **Zero-Shot CoT**：直接加咒语 "Let's think step by step"。
* **Few-Shot (少样本)**：使用 `FewShotPromptTemplate` 给 AI 喂“历史案例”。
    * **原理**：AI 也是模仿大师，通过示例（Examples）学会专家的语气、格式和思考深度。

#### 2. Prompt 拼装结构
一个高级 Prompt 由三部分组成：
1.  **Prefix (前缀)**：立人设（"你是一个 SRE 专家..."）。
2.  **Examples (样本)**：教套路（"遇到 OOM 应该先查 top 再查 logs..."）。
3.  **Suffix (后缀)**：给考题（"当前报错是：{input}，请分析："）。

#### 3. 多变量传递
* 在 `FewShotPromptTemplate` 中，`suffix` 负责承载当前的用户输入。
* 如果输入有多个变量（如 `os_type`, `error_log`），需要在 `input_variables` 中声明，并在 `suffix` 中留出对应的 `{placeholder}`。

### 💻 代码片段
```python
# 强制 AI 慢思考的模板
template = """
你是一个运维专家。请遵循以下步骤分析：
1. **现象分析**: 提取关键报错。
2. **假设排查**: 列出 3 个可能原因。
3. **操作建议**: 给出具体命令。

用户问题: {question}
开始分析:
"""
```

## Day 13: 赋予面孔 (Streamlit UI)

### 🎯 核心目标
从 CLI 命令行工具进化为 Web GUI 应用，理解 Streamlit 独特的运行机制。

### 💡 关键知识点

#### 1. 运行机制：无限重绘 (Rerun)
* **核心逻辑**：只要用户与界面交互（点击按钮、输入文字），**整个 Python 脚本就会从头到尾重新运行一遍**。
* **影响**：普通变量（如 `a = 0`）在重绘后会重置。

#### 2. 状态管理：Session State
* **`st.session_state`**：跨重绘周期的持久化字典。
* **用途**：存储聊天记录 (`messages`)、用户配置、模型对象等不希望被重置的数据。

#### 3. 交互组件
* `st.chat_message`：自动渲染用户/AI 头像和气泡。
* `st.chat_input`：聊天输入框。
* `st.sidebar`：侧边栏布局，适合放 API Key 和文件上传。

### 💻 代码片段
```python
# 典型的 Streamlit 聊天循环
if "messages" not in st.session_state:
    st.session_state.messages = [] # 初始化记忆

# 1. 重绘历史
for msg in st.session_state.messages:
    st.chat_message(msg.type).write(msg.content)

# 2. 处理新输入
if prompt := st.chat_input():
    st.session_state.messages.append(HumanMessage(content=prompt))
    # ... 调用 LLM ...
    st.rerun() # 强制刷新
```


## Day 14: 终极实战 (Jarvis-Ops Pro)

### 🎯 核心目标
整合 LangChain + Streamlit，构建一个支持“文档上传 + 混合增强问答”的完整 AI 产品。

### ☠️ 踩坑与避雷指南 (Troubleshooting)

#### 1. 缓存报错 `UnhashableParamError`
* **错误**：`@st.cache_resource` 装饰了类方法 `def func(self, ...)`。
* **原因**：`self` 包含不可哈希的网络对象。
* **解法**：将缓存逻辑剥离为**独立的静态函数**，不依赖 `self`。

#### 2. 闭包报错 `CacheReplayClosureError`
* **错误**：在缓存函数内部使用了 `st.spinner` 或传入了 `st` 对象。
* **原因**：UI 上下文是临时的，缓存无法在新的上下文中“重放”旧的 UI 操作。
* **解法**：**数据与 UI 分离**。缓存函数只负责纯计算，UI 交互放在调用层。

#### 3. 同名文件更新不提示
* **错误**：仅判断文件名是否存在，导致内容更新后 UI 无反馈。
* **解法**：**时间戳指纹**。缓存函数返回 `(data, timestamp)`，UI 层比对时间戳差异。

#### 4. RAG 的“死板”问题
* **错误**：文档里没有的内容，AI 直接拒绝回答，不符合专家人设。
* **解法**：混合增强 Prompt。设计分层指令：第一优先级查文档，第二优先级用通用知识兜底（但需声明免责）。

### 🚀 架构设计

#### 混合增强 RAG (Hybrid RAG)
为了解决“文档没写 AI 就傻了”的问题，采用了分层 Prompt 策略：
1.  **Level 1**: 优先基于文档回答（引用条款）。
2.  **Level 2**: 文档无记录但属技术问题，使用通用知识兜底（需声明免责）。
3.  **Level 3**: 非技术问题直接拒绝。

### 💻 终极代码结构 (伪代码)
```python
# 1. 独立的缓存函数 (纯数据)
@st.cache_resource
def process_file(file):
    # ... 切片、向量化 ...
    return vectorstore, time.time()

# 2. 主类逻辑 (UI控制)
class App:
    def init_rag(self):
        with st.spinner("处理中..."): # UI 在这里
            db, timestamp = process_file(self.file)
            
            # 智能弹窗逻辑
            if timestamp != st.session_state.last_time:
                st.toast("知识库已更新")
                st.session_state.last_time = timestamp
```