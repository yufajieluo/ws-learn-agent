import os
import operator
from typing import Annotated, Literal, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"

@tool
def multiply(a: int, b: int) -> int:
    '''计算乘法'''
    return a * b

@tool
def get_weather(city: str) -> str:
    '''查询天气'''
    result = None
    if '北京' in city:
        result = '晴，25℃'
    else:
        result = '未知'
    return result

@tool
def get_time() -> str:
    '''获取当前系统时间'''
    import datetime
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return now


tools = [
    multiply,
    get_weather,
    get_time
]

llm = ChatGoogleGenerativeAI(
    model = 'models/gemini-2.5-flash',
    temperature = 0
)
llm_with_tools = llm.bind_tools(tools)

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]

def chatbot(state: AgentState):
    return {
        'messages': [
            llm_with_tools.invoke(state['messages'])
        ]
    }

node_tool = ToolNode(tools = tools)

def should_continue(state: AgentState) -> Literal['tools', '__end__']:
    messages = state['messages']
    last_message = messages[-1]

    if last_message.tool_calls:
        return 'tools'
    else:
        return '__end__'

workflow = StateGraph(AgentState)
workflow.add_node('agent', chatbot)
workflow.add_node('tools', node_tool)
workflow.set_entry_point('agent')
workflow.add_conditional_edges('agent', should_continue)
workflow.add_edge('tools', 'agent')
app_workflow = workflow.compile()

print('🤖 1. 测试普通对话:')
res = app_workflow.invoke(
    {
        'messages': [HumanMessage(content='你好')]
    }
)
print(res['messages'][-1].content)

print("\n🤖 2. 测试工具调用 (数学):")
res = app_workflow.invoke(
    {
        'messages': [HumanMessage(content='11乘以18等于多少？')]
    }
)
print(res['messages'][-1].content)

print("\n🤖 3. 测试工具调用 (天气):")
res = app_workflow.invoke(
    {
        'messages': [HumanMessage(content='北京今天的天气如何？')]
    }
)
print(res['messages'][-1].content)

print("\n🤖 3. 测试工具调用 (天气):")
res = app_workflow.invoke(
    {
        'messages': [HumanMessage(content='上海今天的天气如何？')]
    }
)
print(res['messages'][-1].content)

print("\n🤖 3. 测试工具调用 (时间):")
res = app_workflow.invoke(
    {
        'messages': [HumanMessage(content='现在什么时间？')]
    }
)
print(res['messages'][-1].content)
