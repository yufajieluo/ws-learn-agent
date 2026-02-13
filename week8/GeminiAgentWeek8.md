# 📘 Google Gemini API 开发者实战手册 (Python 版) - Week 8

**版本：** 1.0 (产品化与部署篇)

**时间：** 2026年2月

**适用对象：** AI 全栈工程师 / 产品原型开发者

**核心目标：** 跨越从“本地运行的脚本 Demo”到“带记忆、可视化思考过程的 Web App 产品”的工程鸿沟。

---

## 目录

1.  [Day 33: 海马体植入 (Session Management & Memory)](#day-33-海马体植入-session-management--memory)
2.  [Day 34: 界面版“核按钮” (Human-in-the-loop)](#day-34-界面版-核按钮-human-in-the-loop)
3.  [Day 35: 思考的可视化 (White-box UX & Streamlit)](#day-35-思考的可视化-white-box-ux--streamlit)
4.  [Day 36: 云端发布与依赖地狱 (Cloud Deployment)](#day-36-云端发布与依赖地狱-cloud-deployment)

---

---
## Day 33: 海马体植入 (Session Management & Memory)

### 🎯 核心概念
- **无状态 (Stateless) vs 有状态 (Stateful)**：默认的 Agent 跑完一次代码就清空内存，必须引入 Checkpointer（检查点）才能实现多轮对话。
- **多租户隔离 (Session Isolation)**：企业级应用的核心。通过不同的 `thread_id`，让张三和李四在同一个系统里拥有各自独立、互不干扰的聊天记忆。

### 📝 核心代码
```python
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

# 1. 初始化持久化保存器
conn = sqlite3.connect("agent_memory.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)

# 2. 编译并挂载到图
app = workflow.compile(checkpointer=memory)

# 3. 动态切换会话 ID 调用
config = {"configurable": {"thread_id": "user_123"}}
events = app.stream(inputs, config=config, stream_mode="values")
```

---
## Day 34: 界面版“核按钮” (Human-in-the-loop)

### 🎯 核心概念
- **安全锁 (Safety Valve)**：高危动作（如查阅绝密配置、修改数据库）不能由 AI 完全自主执行，必须引入人工授权 (HITL)。
- **中断机制 (interrupt_before)**：在图执行到指定节点（如 `tools` 节点）之前强行踩刹车，保存状态并退出。

### 📝 核心代码
```python
# 1. 编译时设置刹车点
app = workflow.compile(checkpointer=memory, interrupt_before=["tools"])

# 2. 检查系统是否被拦截
snapshot = app.get_state(config)
if snapshot.next: # 如果有下一步，说明被拦住了
    auth = input("👉 是否授权执行？(y/n): ")
    if auth.lower() == 'y':
        # 3. 授权通过，传入 None 恢复执行
        events_resume = app.stream(None, config=config, stream_mode="values")
```

---

## Day 35: 思考的可视化 (White-box UX & Streamlit)

### 🎯 核心概念
- **黑盒 vs 白盒**：摒弃让用户死等的 Loading 动画，像 OpenAI o1 / DeepSeek R1 一样，将 AI 调用工具的“思考过程”折叠展示在 UI 上。
- **增量流模式 (stream_mode="updates")**：监听图中每个节点的细微动作。字典的 Key 会直接标明刚刚是 `agent` 还是 `tools` 执行完毕。

### 📝 核心代码
```python
# 1. 使用 updates 模式监听节点动作
events = app.stream(inputs, config=config, stream_mode="updates")

for event in events:
    # 2. 拦截大脑 (Agent) 动作
    if "agent" in event:
        ai_msg = event["agent"]["messages"][0]
        if hasattr(ai_msg, "tool_calls") and ai_msg.tool_calls:
            # 渲染一个折叠面板展示工具调用
            with st.status(f"🛠️ 正在调用工具...", expanded=True):
                st.write(ai_msg.tool_calls)
                
    # 3. 拦截机械臂 (Tools) 动作
    elif "tools" in event:
        st.success("✅ 工具调用完成！")
```

### ⚡️ 避坑指南：幽灵气泡 (Ghost Bubbles)

- **现象**：Streamlit 界面上出现了带有头像但完全空白的聊天气泡。
- **原因**：AI 在决定调用工具时，会发出一条携带 `tool_calls` 参数但 `content` 为空的 `AIMessage`。
- **解法**：在前端渲染时，增加 `msg.content.strip()` 的非空判断，屏蔽掉这些只有中间态参数的“隐形消息”。

---

## Day 36: 云端发布与依赖地狱 (Cloud Deployment)
### 🎯 核心概念
- **密码剥离 (Secrets Management)**：上云前绝对不能将 API Key 写死在代码里。必须改为从环境变量或加密仓库中读取。
- **云端部署**：通过 GitHub 联通 Streamlit Community Cloud，实现代码的自动化拉取与部署构建。


### 📝 核心代码
```python
# 安全读取环境变量 (Streamlit 云端标准写法)
import streamlit as st
import os

os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]
```

### ⚡️ 避坑指南：依赖地狱 (Dependency Hell)
- **现象**：本地运行完美，但一上云端构建就全线崩溃报 `ResolutionImpossible`。

- **根本原因**：`pip freeze` 导出的 `requirements.txt` 包含了过度严苛的底层版本锁（如同时锁死互相冲突的 `langchain-core` 版本）。本地能跑往往是因为历史强制安装带来的脆弱平衡。

- **破局之道**：只锁定顶级业务包（如 `streamlit`, `langchain`, `langgraph`），删除所有二级底层依赖，将版本计算的脏活交还给云端的 Pip Resolver 自动去计算最佳兼容组合。