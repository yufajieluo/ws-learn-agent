# 📘 Google Gemini API 开发者实战手册 (Python 版) - Week 10

**版本：** 1.0 (生产调优与 LLMOps 篇)

**时间：** 2026年2月

**适用对象：** AI 全栈工程师 / 产品原型开发者


---

## 目录

1.  [Day 41: 暴力美学 (Long Context & File API)](#day-41-暴力美学-long-context--file-api)
2.  [Day 42: 原生视觉 (Native Vision)](#day-42-原生视觉-native-vision)
3.  [Day 43: 结构化视觉输出 (Visual JSON Mode)](#day-43-结构化视觉输出-visual-json-mode)
4.  [Day 44: 终极毕业设计 (The Ultimate Jarvis)](#day-44-终极毕业设计-the-ultimate-jarvis)

---

## Day 41: 暴力美学 (Long Context & File API)

### 🎯 核心,目标
打破 RAG 的切片限制，利用 Gemini 1.5 Pro/Flash 的 100万+ Token 上下文，直接上传几十页的 PDF 或长视频，让 AI 进行全书跨段落推理。

### 🔑 关键知识点
- **File API**: 对于大文件（PDF/视频），不能直接转文本塞进 Prompt。需要使用 `genai.upload_file` 上传到 Google 临时存储（保存48小时）。
- **网络代理 (Proxy)**: Google API 的文件上传走底层协议，必须在 Python 脚本最开头配置 `os.environ["HTTP_PROXY"]`，否则会报 `TimeoutError`。
- **Token 消耗**: Long Context 虽然精准，但一次对话消耗数万 Token，成本和延迟较高，适合复杂推理场景。

### 📝 核心代码
```python
import google.generativeai as genai

# 1. 上传文件
pdf_file = genai.upload_file("paper.pdf", mime_type="application/pdf")

# 2. 等待处理 (Active 状态)
# ... (省略 wait_for_files_active 函数) ...

# 3. 放入 History
model = genai.GenerativeModel("models/gemini-1.5-flash")
chat = model.start_chat(history=[
    {"role": "user", "parts": [pdf_file, "这篇论文的结论是什么？"]}
])
```

---
## Day 42: 原生视觉 (Native Vision)

### 🎯 核心目标
让 AI 像人类一样“看懂”图片，用于游戏攻略、代码 Debug 或场景描述。

### 🔑 关键知识点
- **多模态输入**: Gemini 是原生多模态模型，可以直接接收图片数据（PIL Image 对象）。
- **无需 OCR**: 不需要先用 OCR 提取文字。模型能理解图片中的文字、物体关系、甚至幽默感（梗图）。
- **Base64 vs File API**: 对于单张小图片，不需要上传到 File API，直接在内存中处理传给模型即可，速度更快。

### 📝 核心代码
```python
import PIL.Image
import google.generativeai as genai

img = PIL.Image.open("zelda_screenshot.jpg")
model = genai.GenerativeModel('models/gemini-1.5-flash')

# 直接把图片和文本放在一个列表里
response = model.generate_content(["看着这张图，告诉我怎么解开这个谜题？", img])
print(response.text)
```

### ⚡️ 避坑指南：幽灵气泡
- **评分标准**：AI 考官的 `Prompt` 必须写清楚评分逻辑（例如：“只要意思对就给 TRUE，不要纠结字面措辞”），否则容易误判。

---

## Day 43: 结构化视觉输出 (Visual JSON Mode)

### 🎯 核心目标
从混乱的非结构化图片（发票、小票、仪表盘）中，精准提取出可编程的 JSON 数据。

### 🔑 关键知识点
- **JSON Mode**: 在 `generation_config` 中设置 `response_mime_type="application/json"`，强制 AI 输出合法的 JSON 字符串。
- **Schema Definition**: 在 Prompt 中通过示例或描述，定义清楚你想要的 JSON 字段（如 `total_amount`, `date`, `items`）。
- **商业价值**: 这是 RPA（流程自动化）的核心技术，可替代传统的正则表达式和模板匹配 OCR。

### 📝 核心代码
```python
model = genai.GenerativeModel(
    'models/gemini-1.5-flash',
    # 强制输出 JSON
    generation_config={"response_mime_type": "application/json"}
)

prompt = """
提取发票信息，格式如下：
{"store": "str", "total": "float", "items": [{"name": "str", "price": "float"}]}
"""

response = model.generate_content([prompt, invoice_img])
data = json.loads(response.text) # 直接转为 Python 字典
```

---

## Day 44: 终极毕业设计 (The Ultimate Jarvis)
### 🎯 核心目标
整合 LangChain、Streamlit、Chroma 和 Gemini，构建一个支持 RAG (文档问答)、持久化记忆、多会话隔离 的完整 AI 助手，并部署到云端。

### 🔑 关键知识点
- **Tech Stack (现代 AI 栈)**:
    - **Frontend**: Streamlit (极速构建 UI)。
    - **Orchestration**: LangChain (管理 Chain 和 Memory)。
    - **Vector DB**: Chroma (本地向量存储，支持 RAG)。
    - **Storage**: SQLite (`SQLChatMessageHistory` 用于存聊天记录)。

- **Session 隔离**: 使用 `session_id` 区分不同用户或对话。在 Streamlit 中通过 `st.session_state` 和 Sidebar 输入框来管理。

- **RAG 流程**: `PyPDFLoader` 加载 -> `RecursiveCharacterTextSplitter` 切分 -> `GoogleGenerativeAIEmbeddings` 向量化 -> `Chroma` 存储 -> `Retriever` 检索。

- **云端部署坑**: 云端容器是临时的，重启后本地文件会丢失。

### 📝 核心代码
```python
# 1. 历史记录工厂 (SQLite)
def get_history(session_id):
    return SQLChatMessageHistory(session_id=session_id, connection="sqlite:///chat.db")

# 2. RAG Chain
rag_chain = (
    RunnablePassthrough.assign(context=lambda x: retriever.invoke(x["question"]))
    | prompt
    | llm
    | StrOutputParser()
)

# 3. 注入历史记录
final_chain = RunnableWithMessageHistory(
    rag_chain,
    get_history,
    input_messages_key="question",
    history_messages_key="history"
)

# 4. 调用
response = final_chain.stream(
    {"question": "我的文档里讲了什么？"},
    config={"configurable": {"session_id": "user_001"}}
)
```