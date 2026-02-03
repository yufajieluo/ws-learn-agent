
# 📘 Google Gemini API 开发者实战手册 (Python 版) - Week 1

**版本：** 1.0 (基础篇)

**时间：** 2026年1月

**适用对象：** DevOps / 后端工程师

**核心目标：** 从零构建具备视觉、工具调用与结构化输出能力的 AI Agent。

---

## 目录
1.  [Day 1: 环境配置与基础认知](#day-1-环境配置与基础认知)
2.  [Day 2: 记忆与人设系统](#day-2-记忆与人设系统)
3.  [Day 3: 赋予双手 (Function Calling)](#day-3-赋予双手-function-calling)
4.  [Day 4: 多模态视觉 (Vision)](#day-4-多模态视觉-vision)
5.  [Day 5: 结构化输出 (JSON Mode)](#day-5-结构化输出-json-mode)
6.  [Day 6: 终极形态 (Agent 架构模式)](#day-6-终极形态-agent-架构模式)
7.  [附录: 常见报错速查](#附录-常见报错速查)

---

## Day 1: 环境配置与基础认知

### 核心知识点
* **API vs 会员**：`Gemini Advanced` 会员权益不包含 API 调用配额。API 开发需要在 Google AI Studio 绑定结算账号 (Pay-as-you-go)。
* **网络问题**：国内开发环境必须在代码中显式配置代理，否则会报 SSL 或 Connection Error。

### 📝 实战代码：Hello World
```python
import google.generativeai as genai
import os

# 1. 网络代理配置 (解决 SSL/Connection Error)
# 请将端口 7890 替换为你实际的代理软件端口
os.environ['http_proxy'] = '[http://127.0.0.1:7890](http://127.0.0.1:7890)'
os.environ['https_proxy'] = '[http://127.0.0.1:7890](http://127.0.0.1:7890)'

# 2. 鉴权配置
# 强烈建议使用环境变量
os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY_HERE"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# 3. 简单调用
# gemini-1.5-flash 是目前速度最快、成本最低的模型，适合开发测试
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content("你好，请用一句话介绍你自己。")
print(response.text)
```

## Day 2: 记忆与人设系统

### 核心知识点
* **System Instruction**：在模型初始化时注入“人设”或“系统级指令”，权重高于普通对话。
* **ChatSession**：`start_chat` 会自动维护 `history` 列表，实现多轮对话记忆。
* **Streaming**：流式输出可以极大降低用户感知的延迟 (TTFT)。

### 📝 实战代码：有性格的对话机器人
```python
# 初始化带有人设的模型
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction="你是一个资深 DevOps 专家，说话风格简洁、犀利，喜欢用计算机术语打比方。"
)

# 开启记忆会话 (history=[] 代表从零开始)
chat = model.start_chat(history=[])

print("--- DevOps Bot Online (输入 'quit' 退出) ---")
while True:
    user_input = input("User: ")
    if user_input.lower() == 'quit': break
    
    # 流式输出
    response = chat.send_message(user_input, stream=True)
    print("AI: ", end='')
    for chunk in response:
        print(chunk.text, end='', flush=True)
    print("\n")
```

## Day 3: 赋予双手 (Function Calling)

### 核心知识点
* **工作原理**：AI 不直接运行代码。AI 输出“调用请求” -> SDK 本地运行 Python 函数 -> SDK 将结果喂回给 AI -> AI 输出最终回复。
* **Docstrings**：函数文档注释是 AI 理解工具用途的唯一途径，必须写清楚参数含义。

### 📝 实战代码：查询模拟服务状态
```python
import time

# 1. 定义工具函数
def get_service_status(service_name: str):
    """
    查询服务的实时运行状态。
    Args:
        service_name: 服务名称 (如 payment-api, db-shard-01)
    """
    print(f"\n[Tool] 正在查询 {service_name} ...")
    time.sleep(1) # 模拟网络请求
    
    # 模拟返回数据
    if "db" in service_name:
        return {"status": "Down", "error": "Connection Timeout"}
    return {"status": "Running", "uptime": "99.9%"}

# 2. 绑定工具
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    tools=[get_service_status]
)

# 3. 开启自动调用模式 (enable_automatic_function_calling=True)
chat = model.start_chat(enable_automatic_function_calling=True)

# AI 会自动决定是否调用工具
response = chat.send_message("帮我看看 db-shard-01 现在挂了吗？")
print(f"AI 回复: {response.text}")
```

## Day 4: 多模态视觉 (Vision)

### 核心知识点
* **原生多模态**：Gemini 能够直接“看”懂图片中的文字、图表趋势、代码逻辑，无需 OCR。
* **调用方式**：将文本 Prompt 和 Image 对象作为一个列表传给模型。
* **注意**：视觉分析通常使用 `generate_content` (无状态) 模式。

### 📝 实战代码：图片分析
```python
import PIL.Image
import google.generativeai as genai
import os

# 配置 API
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# 加载图片 (确保路径正确)
# 实际使用时替换为你的图片路径
img = PIL.Image.open("monitor_screenshot.png")

model = genai.GenerativeModel('gemini-1.5-flash')

prompt = "这是一张 Grafana 监控截图，请分析当前的系统瓶颈在哪里？"

# 发送 [文本, 图片]
response = model.generate_content([prompt, img])
print(response.text)
```

## Day 5: 结构化输出 (JSON Mode)

### 核心知识点
* **Schema 定义**：使用 `typing.TypedDict` 定义严格的数据结构。
* **配置参数**：通过 `generation_config` 强制模型输出 JSON，拒绝自然语言废话。

### 📝 实战代码：日志清洗器
```python
import google.generativeai as genai
import typing_extensions as typing
import json
import os

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# 定义 JSON 结构 (Schema)
class LogEntry(typing.TypedDict):
    timestamp: str
    level: str
    message: str
    root_cause: str

model = genai.GenerativeModel('gemini-1.5-flash')

raw_log = "2026-01-24 14:00:01 [ERROR] Connection timeout to DB-01 due to firewall block"

response = model.generate_content(
    f"提取日志信息: {raw_log}",
    generation_config={
        "response_mime_type": "application/json",
        "response_schema": LogEntry
    }
)

# 直接解析
try:
    data = json.loads(response.text)
    print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print("JSON 解析失败:", e)
```

## Day 6: 终极形态 (Agent 架构模式)

### 核心模式：End-Game Tool Pattern (结案工具模式)
解决同时需要“复杂思考/查工具”和“严格 JSON 输出”时的冲突问题。

**逻辑流：** 观察(Vision) -> 思考 -> 查工具(Worker Tool) -> 综合 -> **调用结案工具(End-Game Tool)** -> 提取参数。

### 📝 实战代码：DevOps 智能体 (完整版)
```python
import os
import json
import time
import typing_extensions as typing
import PIL.Image
import google.generativeai as genai

# 配置 API
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# --- 1. 定义数据结构 ---
class IncidentReport(typing.TypedDict):
    incident_id: str
    service_name: str
    root_cause: str
    action_plan: str
    severity: typing.Literal['Critical', 'Warning', 'Info']

# --- 2. 定义工具 ---
def fetch_logs(service_name: str) -> str:
    """查询服务日志"""
    print(f"\n[🛠️ Worker Tool] 查询 {service_name} 日志...")
    time.sleep(1)
    # 模拟工具返回：如果是 node 服务，返回磁盘错误
    if "node" in service_name:
        return "ERROR: Disk I/O wait > 800ms" 
    return "INFO: Healthy"

def submit_final_report(report: IncidentReport):
    """
    当调查结束时，调用此工具提交最终报告。
    """
    print("\n[✅ End-Game Tool] 报告已提交 (数据已拦截)")
    return "Success"

# --- 3. 初始化 Agent ---
tools = [fetch_logs, submit_final_report]
model = genai.GenerativeModel('gemini-1.5-flash', tools=tools)
chat = model.start_chat(enable_automatic_function_calling=True)

# --- 4. 执行逻辑 ---
def run_agent(image_path):
    if not os.path.exists(image_path):
        print("图片不存在")
        return

    img = PIL.Image.open(image_path)
    
    # 关键 Prompt：强制流程 + 强制结束语 "DONE"
    prompt = """
    系统指令：
    1. 你是 DevOps 专家，请分析图片异常。
    2. 使用 `fetch_logs` 查询相关服务日志。
    3. 综合信息，构造 `IncidentReport` 对象。
    4. **必须**调用 `submit_final_report` 提交报告。
    5. 工具调用成功后，你必须向用户输出一个单词："DONE"，以结束任务。
    """
    
    print("🤖 Agent 启动...")
    chat.send_message([prompt, img])
    
    # --- 5. 数据提取 (从历史记录中把 JSON 抠出来) ---
    json_data = None
    # 倒序遍历，找到最后一次提交
    for part in reversed(chat.history):
        if part.role == 'model' and part.parts[0].function_call:
            fc = part.parts[0].function_call
            if fc.name == 'submit_final_report':
                print("\n🎁 === 成功捕获 JSON ===")
                # 提取参数
                if 'report' in fc.args:
                    json_data = fc.args['report']
                    # 兼容性处理
                    if not isinstance(json_data, dict):
                         json_data = dict(json_data)
                break
    
    if json_data:
        print(json.dumps(json_data, indent=2, ensure_ascii=False))
    else:
        print("❌ 未能提取到 JSON")

# 使用方法：确保目录下有图片
# run_agent("test_image_4.png")
```

## 附录: 常见报错速查

| 错误代码 / 现象 | 原因 | 解决方案 |
| :--- | :--- | :--- |
| **SSL: UNEXPECTED_EOF** | Python 脚本未走代理，连接被防火墙阻断。 | 在代码开头设置 `os.environ['https_proxy']`。 |
| **400 BadRequest (Json Mode)** | 同时开启了 `function_calling` 和 `response_mime_type: json`。 | 移除 `response_mime_type`，改用 **Day 6 的 End-Game Tool 模式**。 |
| **死循环 (Infinite Loop)** | AI 一直调工具，不知道如何结束。 | 修改 Prompt，要求 AI 在提交工具后显式输出特定文本（如 "DONE"）。 |
| **429 Resource Exhausted** | 免费层级 (Free Tier) 触发了速率限制。 | 绑定结算账号升级为 Pay-as-you-go，或代码中增加 `time.sleep`。 |
| **Google Generative AI SDK 报错** | SDK 版本过旧。 | 运行 `pip install -U google-generativeai` 更新。 |