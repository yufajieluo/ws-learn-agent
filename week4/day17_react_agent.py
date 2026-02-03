
import os

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"

@tool
def get_current_time(location: str = 'China'):
    '''
    当用户询问当前时间、日期时，必须调用此工具。
    '''
    import datetime
    # 为了演示 ReAct 的观察能力，我们模拟一个不同的时间
    # 假设现在是深夜，触发不同的逻辑
    return "2026-02-02 23:30:00"

@tool
def calculate_power(base: float, exponent: float):
    '''计算幂运算 (base 的 exponent 次方)'''
    return str(base ** exponent)

tools = [get_current_time, calculate_power]

llm = ChatGoogleGenerativeAI(
    model='models/gemini-2.5-flash', 
    temperature=0
)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "你是一个非常有用的 AI 助手。你有权访问以下工具，请在需要时使用它们来回答用户的问题。",
    ),
    ("user", "{input}"),
    # agent_scratchpad 是 Agent 思考过程的占位符，必须保留！
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True
)

print("🤖 Jarvis ReAct 系统启动...\n")

query = """
请帮我检查一下现在的时间。
如果时间晚于 22:00 (晚上10点)，请计算 2 的 10 次方来打发时间。
如果时间早于 22:00，就告诉我“该睡觉了”，不要做计算。
"""

result = agent_executor.invoke({"input": query})

print("\n🏁 最终回答：")
print(result['output'])
print("--------------------------------------------------")