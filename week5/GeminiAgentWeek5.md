# 📘 Google Gemini API 开发者实战手册 (Python 版) - Week 5

**版本：** 1.0 (图编排篇)

**时间：** 2026年2月

**适用对象：** AI 工程师 / 架构师 / 高级 Python 开发者

**核心目标：** 掌握 LangGraph 框架，构建可控、持久化、支持人机协作（HITL）的企业级 Agent。

---

## 目录

1.  [Day 19: 拒绝黑盒 (Hello Graph)](#day-19-拒绝黑盒-hello-graph)
2.  [Day 20: 智能分流 (Conditional Edges)](#day-20-智能分流-conditional-edges)
3.  [Day 21: 记忆存档 (Persistence)](#day-21-记忆存档-persistence)
4.  [Day 22: 人机接力 (Human-in-the-loop)](#day-22-人机接力-human-in-the-loop)

---

## Day 19: 拒绝黑盒 (Hello Graph)

**核心目标：** 理解 **DAG (有向无环图)** 与 **State Machine (状态机)** 的概念，从 `AgentExecutor` 的“全自动黑盒”转向 `StateGraph` 的“精细化编排”。

### 1. 核心概念
LangGraph 的核心思想是：**把 AI 的思考过程画成一张流程图。**
* **AgentExecutor (Week 4)**: 类似于“自动驾驶”。你给个目标，它自己开，但容易开进沟里。
* **LangGraph (Week 5)**: 类似于“铺设铁轨”。你规定好每一站怎么走，车只能沿着铁轨跑。

### 2. 关键组件

#### State (状态)
全图共享的内存空间，通常是一个 `TypedDict`。
* 它像工厂流水线上的“托盘”。
* 每个节点从托盘拿数据，处理完再放回托盘。

#### Node (节点)
Python 函数，负责干活。
* **输入**: 当前的 State。
* **输出**: 想要更新的字段 (Dict)。

#### Edge (边)
确定性的流向。
* `add_edge("Node_A", "Node_B")`: A 做完**必须**去 B。

### 3. 代码骨架

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

# 1. 定义状态
class MyState(TypedDict):
    text: str
    count: int

# 2. 定义节点函数
def node_a(state: MyState):
    return {"text": "Hello"}

# 3. 组装图
workflow = StateGraph(MyState)
workflow.add_node("node_a", node_a)
workflow.set_entry_point("node_a") # 入口
workflow.add_edge("node_a", END)   # 出口 (结束运行)

app = workflow.compile()
```

### 4. 学习心得
- ***显式优于隐式*** - 在 LangGraph 里，没有任何魔法。所有的跳转逻辑都是你一行行代码写出来的，这让调试变得非常容易。
- ***State 是核心*** - 设计 Graph 的第一步永远是设计 State。想清楚要在节点间传递什么数据，图就画出来了一半。

---
## Day 20: 智能分流 (Conditional Edges)

**核心目标：** 引入 **Router (路由器)** 和 **Cycle (循环)**，让 Agent 具备自我修正（Self-Correction）的能力。

### 1. 核心技术：条件边
普通边是单行道，条件边是十字路口。
* **Source**: 谁做完后决定？(例如：老师节点)
* **Router**: 决策函数。(例如：判断分数是否及格)
* **Map**: 映射表。(及格 -> END, 不及格 -> 重做)

### 2. 关键神器：Reducer (`operator.add`)
在 `TypedDict` 中，默认行为是 **覆盖 (Override)**。但在聊天记录场景中，我们需要 **追加 (Append)**。

```python
import operator
from typing import Annotated

class ChatState(TypedDict):
    # 🔥 关键：告诉 LangGraph，新的 list 不要覆盖旧的，而是加到后面
    messages: Annotated[list, operator.add]
```

### 3. 学习心得
- ***死循环***
    - 现象
        `GraphRecursionError: Recursion limit of 25 reached`
    - 解法
        1. 在 `router` 函数里增加硬性逻辑：`if retries > 3: return END`
        2. 调试时可调大限制：`app.invoke(..., config={"recursion_limit": 50})`


---
## Day 21: 记忆存档 (Persistence)

**核心目标：** 为图加上 **Checkpointer (存档器)**，赋予 Agent **长期记忆**和**跨会话隔离**的能力。

### 1. 核心概念：Thread ID
LangGraph 通过 `config` 区分不同的用户或会话。
```python
config = {"configurable": {"thread_id": "user_123"}}
```
`thread_id` 就是数据库的主键。只要 ID 不变，LangGraph 就能从数据库里把之前的聊天记录捞出来继续聊。

### 2. 存储后端选择
- `MemorySaver`: 存内存。程序重启就丢。适合写 Demo。

- `SqliteSaver`: 存本地文件。适合单机开发、测试。

- `PostgresSaver`: 存数据库。适合生产环境，支持高并发。

### 3. 学习心得
- ***神秘的 .wal 文件***
    - 现象
    目录下突然出现 `.sqlite-wal` 和 `.sqlite-shm` 文件。
    - 解答
    这是 SQLite 的 WAL (Write-Ahead Logging) 高性能模式日志。
        - 千万别删！ 里面存着还没合并到主文件的最新数据。
        - 程序正常关闭时，它们会自动消失（或合并）。

- ***Checkpointer 是无感的*** - 只要配置好了，你在写 Node 函数时完全不需要关心存取数据库的逻辑，直接操作 State 即可。

---

## Day 22: 人机接力 (Human-in-the-loop)

**核心目标：** 实现 Agent 开发的圣杯功能：**断点续传**与**人工干预**。让 AI 在关键节点停下来，等待人类审批或修改。

### 1. 核心机制

#### 暂停 (`interrupt_before`)
```python
app = workflow.compile(checkpointer=memory, interrupt_before=["publisher"])
```
系统会在执行 publisher 节点之前，自动存盘并退出进程

#### 篡改 (`update_state`)
```python
app.update_state(config, {"content": "老板修改后的文案"}, as_node="writer")
```
在暂停期间，人类可以直接修改数据库里的 State，假装是上一个节点生成的。

### 2. 恢复执行的终极陷阱
#### ❌ 错误做法：传入空字典 `{}`
```python
app.invoke({}, config=thread_config)
```
- ***LangGraph 视角*** - 用户传了新数据 `{}`，这代表要发起一次新的交互。
- ***后果*** - 流程可能会从头开始 (Restart)，或者重新运行 Entry Point，导致人类的修改被覆盖。

#### ✅ 正确做法：传入 ```None```
```python
app.invoke(None, config=thread_config)
```
- ***LangGraph 视角*** - 用户没传数据 (`None`)，这代表要继续 (Resume) 上次没跑完的流程。”
- ***后果*** - 直接跳过已完成的节点，执行 `Next` 节点 (Publisher)。

### 3. 学习心得
- ***State is King*** - 只要控制了 State（通过 `update_state`），你就控制了 Agent 的一切。
- ***None 的重要性*** - 在 LangGraph 中，`None` 输入是唯一的“继续执行”信号。