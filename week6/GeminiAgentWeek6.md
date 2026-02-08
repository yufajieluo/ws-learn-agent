# 📘 Google Gemini API 开发者实战手册 (Python 版) - Week 6

**版本：** 1.0 (全栈应用篇)

**时间：** 2026年2月

**适用对象：** 全栈 AI 工程师 / 产品原型开发者

**核心目标：** 将本地运行的 LangGraph 智能体封装为标准 RESTful API，构建支持流式输出（Streaming）的现代 Web 前端，并实现公网发布与多用户记忆隔离。

---

## 目录

1.  [Day 24: 接口服务化 (LangServe API)](#day-24-接口服务化-langserve-api)
2.  [Day 25: 微服务架构 (Client-Server Pattern)](#day-25-微服务架构-client-server-pattern)
3.  [Day 26: 极致体验 (Streaming UX)](#day-26-极致体验-streaming-ux)
4.  [Day 27: 云端发布 (Production Launch)](#day-27-云端发布-production-launch)

---

---
## Day 24: 接口服务化 (LangServe API)

### 🎯 核心目标
解决 LangServe 自带调试界面 (Playground) 白屏报错的问题，理解 Pydantic Schema 在前后端交互中的作用。

### 📝 关键知识点

#### 1. 端口号陷阱
- **现象**: 控制台打印 `Running on 8000`，但实际代码写的是 `uvicorn.run(..., port=8001)`。
- **教训**: 必须确保打印的提示信息与实际运行端口一致，避免访问错误的地址。

#### 2. Playground 白屏原因
- **错误**: `[Error] Error: Unknown type: {"type":"null"}`
- **原理**: LangServe 会根据 Python 类型提示 (`Optional[str] = None`) 自动生成前端表单。如果没有明确定义输入结构，它会尝试渲染所有字段（包括内部变量 `answer`），导致 React 前端渲染崩溃。

#### 3. 解决方案：InputSchema
使用 `pydantic.BaseModel` 定义一个干净的“输入菜单”，只暴露用户需要填写的字段。

```python
from pydantic import BaseModel
from typing import List
from langchain_core.messages import BaseMessage

# 定义给前端看的输入格式
class InputSchema(BaseModel):
    problem: str
    messages: List[BaseMessage] = [] # 允许为空

# 绑定到 Agent
app_agent = workflow.compile(checkpointer=memory)
app_agent = app_agent.with_types(input_type=InputSchema) # 关键代码
```

---
## Day 25: 微服务架构 (Client-Server Pattern)

### 🎯 核心目标
模拟大厂开发模式，将 AI 大脑 (Backend) 与 用户界面 (Frontend) 分离，通过 HTTP API 通信。

### 🏛️ 架构设计
- **Backend (服务端)**: 运行在 `8001` 端口。负责逻辑推理 (LangGraph + FastAPI)。
- **Frontend (客户端)**: 运行在 `8501` 端口。负责界面展示 (Streamlit)。
- **通信协议**: HTTP REST API (`requests.post`).

### 📝 关键代码与坑

#### 1. Streamlit 启动规则
`st.set_page_config()` **必须** 是脚本中的第一条 Streamlit 命令，否则会直接报错。

#### 2. Payload 构造 (422 错误修复)
前端发送的数据必须严格符合后端 `InputSchema` 的定义。
```python
# client.py
payload = {
    "input": {
        "problem": user_input,
        "messages": [] 
    },
    "config": {
        "configurable": {
            "thread_id": thread_id # 必须传 ID，否则无法隔离用户
        }
    }
}
response = requests.post(API_URL, json=payload) # 必须用 /invoke 接口
```

#### 3. 进阶技巧
- 为了防止前端漏传 `thread_id` 导致后端崩溃，在后端增加 `per_req_config_modifier` 进行兜底拦截。
- 如果 LangServe 自动解析失败，可以使用 `await request.json()` 手动解析 Body。

---
## Day 26: 极致体验 (Streaming UX)

### 🎯 核心目标
抛弃傻等的 `requests.post`，使用 LangChain 的 `RemoteRunnable` 实现类似 ChatGPT 的打字机/流式效果。

### 🌊 核心技术：Server-Sent Events (SSE)

#### 1. RemoteRunnable
它能把远程 API 伪装成本地对象，让我们能调用 `.stream()` 方法。
```python
from langserve import RemoteRunnable

# 连接后端（注意：不需要加 /invoke 或 /stream，只需到根路径）
remote_agent = RemoteRunnable("[http://127.0.0.1:8001/math](http://127.0.0.1:8001/math)")

# 像调用本地链一样调用远程链
for chunk in remote_agent.stream(inputs, config=config):
    # 处理 chunk...
```

#### 2. 可视化思考过程
使用 Streamlit 的 `st.status` 创建一个可折叠的状态面板，实时展示 AI 的思考步骤（学生做题 -> 老师判卷 -> 重试）

#### 3. 对象属性访问陷阱
- **错误**: `'AIMessage' object is not subscriptable`
- **原因**: `RemoteRunnable` 会自动把 JSON 反序列化为对象。
- **解决**: 使用点号访问属性 (`msg.content`) 而不是字典下标 (`msg['content']`)。

---

## Day 27: 云端发布 (Production Launch)

### 🎯 核心目标
使用 `ngrok` 将本地服务发布到公网，并修复“AI 记不住用户提问”的逻辑 Bug。

### ☁️ 内网穿透 (ngrok)
- **原理**: 在本地防火墙打一条“地道”连接到 ngrok 服务器。
- **命令**: `ngrok http 8501` (暴露前端端口)。
- **结果**: 获得一个 `https://....ngrok-free.app` 的公网链接，手机/朋友均可访问。

### 🧠 记忆丢失 Bug 修复
- **现象**: 只有 AI 的回答被存入数据库，用户的提问 (`problem`) 仅作为临时变量，没存入 `messages` 列表。
- **后果**: AI 只有答案的记忆，不知道这个问题对应什么，导致多轮对话失效。
- **修复**: 在 `node_student` 返回时，手动构造 `HumanMessage`。

```python
# server_langserve.py - node_student
from langchain_core.messages import HumanMessage

# ... 
# 修复前: return {"messages": [response]}
# 修复后: 显式保存用户问题和 AI 回答
return {
    "messages": [
        HumanMessage(content=problem), # 补上这一句！
        response
    ]
}
```