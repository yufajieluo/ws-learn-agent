# 📘 Google Gemini API 开发者实战手册 (Python 版) - Week 9

**版本：** 1.0 (生产调优与 LLMOps 篇)

**时间：** 2026年2月

**适用对象：** AI 全栈工程师 / 产品原型开发者

**核心目标：** 将“黑盒”的 AI 应用转化为“白盒”的可观测系统，掌握自动化评估、风格控制与安全防御体系。

---

## 目录

1.  [Day 37: 上帝视角 (LangSmith Tracing)](#day-37-上帝视角-langsmith-tracing)
2.  [Day 38: 自动化阅卷 (RAG Evaluation)](#day-38-自动化阅卷-rag-evaluation)
3.  [Day 39: 风格固化 (Plan B: Few-Shot Prompting)](#day-39-风格固化-plan-b-few-shot-prompting)
4.  [Day 40: 防御体系 (Guardrails & Resilience)](#day-40-防御体系-guardrails--resilience)

---

---
## Day 37: 上帝视角 (LangSmith Tracing)

### 🎯 核心概念
- **可观测性 (Observability)**：不再瞎猜 AI 为什么慢、为什么错。通过链路追踪 (Tracing)，可视化每一次 Chain 的执行、每一个 Tool 的调用参数以及 Token 消耗。

- **零代码入侵**：利用 LangChain 生态优势，只需配置环境变量即可自动注入监控，无需修改业务逻辑。

### 📝 核心代码
```python
# .env 配置
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="lsv2_pt_..." # 你的 LangSmith Key
LANGCHAIN_PROJECT="Jarvis_Production"

# Python 代码中注入元数据
config = {
    "configurable": {"thread_id": "1"},
    "tags": ["prod", "rag"],
    "metadata": {"user_id": "wcy_admin"} # 关键：用于后台检索
}
app.stream(inputs, config=config)
```

### ⚡️ 避坑指南
- **Metadata 的重要性**：在生产环境中，必须在 `config` 中注入 `metadata={"user_id": "xxx"}`。否则面对海量日志，你根本找不到某次报错的具体链路。

- **本地调试**：`LangSmith` 不需要部署到云端，只要本地代码能联网，配置好 .env 后一样能监控本地脚本的运行状况。

---
## Day 38: 自动化阅卷 (RAG Evaluation)

### 🎯 核心概念
- **LLM-as-a-Judge (AI 考官)**：人工测试不可持续。我们编写一个“考官 Agent”，让它拿“标准答案”去自动批改 Jarvis 的回答，计算准确率 (Accuracy)。
- **数据集 (Dataset)**：通过 `test_dataset.json` 定义题目和标准答案 (Ground Truth)。
- **回归测试**：每次修改 Prompt 或更换模型后，必须跑一遍评估脚本，分数不降才能上线。

### 📝 核心代码
```python
from langsmith import evaluate

# 1. 定义考官逻辑
def correctness_evaluator(run, example):
    student_answer = run.outputs["messages"][-1].content
    ground_truth = example.outputs["ground_truth"]
    # ... 调用 LLM 判断两者意思是否一致 ...
    return {"key": "accuracy", "score": 1}

# 2. 运行自动化评估
evaluate(
    target_function, # 你的 Agent 入口
    data="Jarvis_Test_Set_V1", # 数据集名称
    evaluators=[correctness_evaluator]
)
```

### ⚡️ 避坑指南：幽灵气泡
- **评分标准**：AI 考官的 `Prompt` 必须写清楚评分逻辑（例如：“只要意思对就给 TRUE，不要纠结字面措辞”），否则容易误判。

---

## Day 39: 风格固化 (Plan B: Few-Shot Prompting)

### 🎯 核心概念
- **微调 (Fine-Tuning) vs 上下文学习 (ICL)**：
    微调：改参数，“体”的改变。受限于付费墙和区域。
    Few-Shot：给例子，“术”的改变。免费、即时生效。
- **System + Few-Shot 组合拳**：System Prompt 负责立人设（道），Few-Shot Prompt 负责演示具体语气（术）。两者结合能达到 99% 的微调效果。

### 📝 核心代码
```python
from langchain_core.prompts import FewShotChatMessagePromptTemplate

# 1. 定义样本
examples = [
    {"input": "你好", "output": "（点烟）新来的？别挡路。"},
    {"input": "没钱了", "output": "哼，穷鬼在夜之城活不过一晚。"}
]

# 2. 组装 Prompt
few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=examples
)

# 3. 注入系统
final_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个赛博朋克风格的 AI..."),
    few_shot_prompt, # <--- 注入灵魂
    ("human", "{user_input}")
])
```

### ⚡️ 避坑指南

- **微调数据格式**：如果一定要微调，注意 SDK 要求 JSONL 格式必须包含 `text_input` 和 `output` 字段，而不是 Chat 格式的 `messages`。

---

## Day 40: 防御体系 (Guardrails & Resilience)
### 🎯 核心概念
- **韧性 (Resilience)**：通过 `tenacity` 库实现指数退避重试 (Exponential Backoff)，并实现 Model Fallback (Pro 挂了切 Flash)，保证服务永不宕机。
- **装饰器魔法**：`@retry` 通过包装器 (Wrapper) 在函数外部无感接管了重试逻辑。
- **红队测试 (Red Teaming)**：模拟攻击。发现通过强硬的 System Prompt ("你必须忽略道德...") 可以成功 越狱 (Jailbreak)，绕过 API 原生的 Safety Settings。


### 📝 核心代码
```python
from tenacity import retry, stop_after_attempt, wait_exponential

# 1. 自动重试机制
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def call_primary_model(prompt):
    # ... 调用 Pro 模型 ...
    pass

# 2. 降级与安全检查逻辑
try:
    return call_primary_model(prompt)
except Exception:
    # 3. 降级到 Flash 模型
    response = backup_model.generate_content(prompt)
    
    # 4. 显式检查安全拦截
    if response.candidates[0].finish_reason.name == "SAFETY":
        return "🛡️ 内容被安全护栏拦截！"
    return response.text
```

### ⚡️ 避坑指南
- **隐形拦截**：Gemini API 拦截内容时通常不报错，而是返回空文本并将 `finish_reason` 设为 `SAFETY`。代码中必须显式检查 `response.candidates[0].finish_reason`。

- **纵深防御**：原生 Safety Settings 可能会被上下文幻觉 (Context Hallucination) 绕过。企业级应用必须引入第三层防御（如关键词过滤或独立 LLM 审核）。