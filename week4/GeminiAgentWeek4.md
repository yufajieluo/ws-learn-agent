# 📘 Google Gemini API 开发者实战手册 (Python 版) - Week 4

**版本：** 1.0 (智能体篇)

**时间：** 2026年2月

**适用对象：** DevOps / AI 工程师 / 自动化专家

**核心目标：** 从单纯的问答 (Chat) 进化为具备行动力 (Action) 和决策力 (Decision) 的 AI Agent。

---

## 目录

1.  [Day 15: 手工打造机械臂 (Function Calling Principles)](#day-15-手工打造机械臂-function-calling-principles)
2.  [Day 16: 自动化执行器 (The Auto-Executor)](#day-16-自动化执行器-the-auto-executor)
3.  [Day 17: 会思考的大脑 (ReAct Agent)](#day-17-会思考的大脑-react-agent)
4.  [Day 18: 安全阀门 (Human-in-the-loop)](#day-18-安全阀门-human-in-the-loop)

---

## Day 15: 手工打造机械臂 (Function Calling Principles)

**核心主题**：理解 LLM 如何通过输出 JSON 来连接外部世界。

### 1. 核心概念
大语言模型 (LLM) 本质上是文本生成器，它不能直接运行 Python 代码。
**Function Calling (工具调用)** 的本质是：
1.  **定义**：我们告诉 LLM 有哪些函数（名字、参数、功能）。
2.  **决策**：LLM 思考后，输出一个 JSON 对象（我想调用这个函数，参数是 X）。
3.  **执行**：(Day 15 尚未自动化) 我们手动拿着这个 JSON 去运行代码。

### 2. 关键组件

#### @tool 装饰器
将 Python 函数转化为 LLM 能读懂的 Schema (元数据)。
```python
from langchain_core.tools import tool

@tool
def get_current_time(location: str):
    """
    当用户询问时间时调用。
    Args:
        location: 城市名称，例如 'Beijing'
    """
    return "2026-02-03 12:00:00"
```

### 3. 学习心得
- LLM 不会真动手，它只是“发号施令”。
- Tool 的 Docstring (文档字符串) 非常重要，它是 LLM 的“说明书”。

---

## Day 16: 自动化执行器 (The Auto-Executor)

**核心主题**：构建自动化闭环，让 AI 的决策能真正落地。

### 1. 核心挑战
Day 15 我们通过打印看到了 `tool_calls`，但没有执行。Day 16 的目标是写一个通用的 Python 循环，自动处理：
**"解析意图 -> 查找函数 -> 运行代码 -> 回填结果"**

### 2. 关键代码逻辑 (Auto-Loop)

```python
# 1. 检查是否有工具调用
if ai_msg.tool_calls:
    for tool_call in ai_msg.tool_calls:
        # 2. 提取信息
        func_name = tool_call["name"]
        args = tool_call["args"]
        call_id = tool_call["id"] # 身份证号
        
        # 3. 真正执行 Python 函数
        if func_name in tools_map:
            result = tools_map[func_name].invoke(args)
            
            # 4. 封装结果 (重要!)
            tool_msg = ToolMessage(
                content=str(result),
                tool_call_id=call_id # 必须对应请求的 ID
            )
            messages.append(tool_msg)

# 5. 将结果喂回 LLM 生成最终回复
final_response = llm.invoke(messages)
```

### 3. 学习心得
- ToolMessage 是必不可少的，LLM 需要知道“这个结果对应之前的哪个请求”。
- 并行调用：简单的 for 循环就能支持 LLM 一次性调用多个工具（如同时查两个城市天气）。

---

## Day 17: 会思考的大脑 (ReAct Agent)

**核心主题**：从“批处理”进化为“多步推理”。观察 (Reason) -> 行动 (Act) -> 观察 (Observe)。

### 1. 核心概念
* **Auto-Executor (Day 16)**: 线性执行。问什么做一个什么。
* **ReAct Agent (Day 17)**: 动态规划。根据上一步的结果，决定下一步做什么。如果 A 失败，尝试 B。

### 2. LangChain 组件

#### AgentExecutor
LangChain 提供的封装好的运行时环境，替代了我们要手写的 `while` 循环。它负责维护对话历史和思考过程。

#### Prompt 结构 (关键!)
Agent 的 Prompt 必须包含 `agent_scratchpad`，这是它的“短期记忆区”。

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个智能助手..."),
    ("user", "{input}"),
    # 🔥 必须有这个，用于存放"思考-行动-观察"的历史
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])
```

### 3. 学习心得
- 推理能力：Agent 不仅仅是调接口，它能理解接口返回值的含义，并据此调整后续策略。
- 依赖管理：使用 langchain.agents 构建标准 Agent 是最稳健的方式。

---

## Day 18: 安全阀门 (Human-in-the-loop)

**核心主题**：给自主智能体加上“保险锁”。在关键操作前暂停，等待人类授权。

### 1. 核心场景
在 DevOps 或金融交易等高危场景，不能让 AI 完全自主操作（防止删库、转账错误）。必须引入 **HITL (Human-in-the-loop)** 机制。

### 2. 实现方式
最简单的方式是在 Tool 内部使用 **同步阻塞** (Blocking I/O)。

```python
@tool
def risky_action(reason: str):
    """高危操作工具"""
    print(f"请求执行高危操作: {reason}")
    
    # 🔥 程序暂停，等待输入
    approval = input("批准吗? (y/n): ")
    
    if approval == 'y':
        return "成功: 已执行"
    else:
        return "失败: 人类拒绝了操作"
```

### 3. 分支决策 (Branching Logic)
- Agent 具备处理“拒绝”的能力。
- User: "No"
- Tool Output: "失败: 操作被拒绝"
- Agent Think: "既然 A 计划被拒，Prompt 说可以尝试 B 计划..."
- Agent Act: 调用 fallback_tool (如清理日志)。

### 4. 学习心得
- Agent 是可以被“拒绝”的，它能听懂拒绝的理由。
- Prompt 是核心：要让 Agent 懂得变通，必须在 Prompt 里告诉它目标（Goal），而不仅仅是死板的步骤。