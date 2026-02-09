import os
import operator
from typing import Annotated, Literal, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

#-------------
import requests
old_request = requests.Session.request

def new_request(self, method, url, *args, **kwargs):
    # 强制把 verify 设置为 False
    kwargs['verify'] = False
    return old_request(self, method, url, *args, **kwargs)

# 3. 覆盖回去
requests.Session.request = new_request
#-------------

os.environ['GOOGLE_API_KEY'] = 'YOUR_GOOGLE_API_KEY'
os.environ['TAVILY_API_KEY'] = 'YOUR_TAVILY_API_KEY'

search_tool = TavilySearchResults(max_results = 2)

tools = [
    search_tool
]

llm = ChatGoogleGenerativeAI(
    model = 'models/gemini-2.5-flash',
    temperature = 0
)
llm_with_tools = llm.bind_tools(tools)

class AgentState(TypedDict):
    messages: Annotated[list[HumanMessage], operator.add]

def node_chatbot(state: AgentState):
    return {
        'messages': [
            llm_with_tools.invoke(state['messages'])
        ]
    }

node_tool = ToolNode(tools = tools)

def should_continue(state: AgentState) -> Literal['tools', '__end__']:
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return 'tools'
    else:
        return '__end__'

workflow = StateGraph(AgentState)
workflow.add_node('agent', node_chatbot)
workflow.add_node('tools', node_tool)
workflow.set_entry_point('agent')
workflow.add_conditional_edges('agent', should_continue)
workflow.add_edge('tools', 'agent')

app_workflow = workflow.compile()

print("🔎 正在联网搜索...")
query = "现在英伟达 (NVDA) 的股价是多少？并告诉我最新发生了什么相关大新闻？请同时附上股价时间及新闻时间"
final_state = app_workflow.invoke(
    {
        'messages': [HumanMessage(content=query)]
    }
)
print("\n🤖 AI 回答:")
print(final_state['messages'][-1].content)

print("\n👀 中间搜索结果 (Tool Output):")
for msg in final_state['messages']:
    if hasattr(msg, 'tool_calls') and len(msg.tool_calls) > 0:
        print(f'🛠️ AI 请求调用工具: {msg.tool_calls[0]['name']}')
    if msg.type == 'tool':
        print(f'📄 搜索到的内容片段: {msg.content[:200]}...')

print(f'\n--------------------------------------------------\n')
query = "现在贵州茅台的股价是多少？并告诉我最新发生了什么相关大新闻？请同时附上股价时间及新闻时间"
final_state = app_workflow.invoke(
    {
        'messages': [HumanMessage(content=query)]
    }
)
print("\n🤖 AI 回答:")
print(final_state['messages'][-1].content)

print("\n👀 中间搜索结果 (Tool Output):")
for msg in final_state['messages']:
    if hasattr(msg, 'tool_calls') and len(msg.tool_calls) > 0:
        print(f'🛠️ AI 请求调用工具: {msg.tool_calls[0]['name']}')
    if msg.type == 'tool':
        print(f'📄 搜索到的内容片段: {msg.content[:200]}...')

print(f'\n--------------------------------------------------\n')
query = "请搜索今天关于 'OpenAI' 的最新 3 条新闻，并用中文总结给我，请附上新闻发布的时间。"
final_state = app_workflow.invoke(
    {
        'messages': [HumanMessage(content=query)]
    }
)
print("\n🤖 AI 回答:")
print(final_state['messages'][-1].content)

print("\n👀 中间搜索结果 (Tool Output):")
for msg in final_state['messages']:
    if hasattr(msg, 'tool_calls') and len(msg.tool_calls) > 0:
        print(f'🛠️ AI 请求调用工具: {msg.tool_calls[0]['name']}')
    if msg.type == 'tool':
        print(f'📄 搜索到的内容片段: {msg.content[:200]}...')