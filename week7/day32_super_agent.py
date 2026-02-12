import os
import operator
import requests
from typing import Annotated, Literal, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools.retriever import create_retriever_tool
from langchain_core.tools import Tool
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

os.environ['GOOGLE_API_KEY'] = 'YOUR_GOOGLE_API_KEY'
os.environ['TAVILY_API_KEY'] = 'YOUR_TAVILY_API_KEY'

PERSIST_DIR = 'day30_chroma_db_data'

print('🔄 正在装配 Super Agent...')

embedding_function = GoogleGenerativeAIEmbeddings(
    model = 'models/gemini-embedding-001',
    task_type = 'retrieval_query'
)

vectorstore = Chroma(
    persist_directory=PERSIST_DIR,
    embedding_function=embedding_function
)

retriever = vectorstore.as_retriever(
    search_kwargs = {'k':3}
)

tool_internal = create_retriever_tool(
    retriever=retriever,
    name = 'search_internal_knowledge',
    description = '【绝密】仅用于查询公司内部 AI 助手 "Jarvis" 的配置、IP地址、开发者或紧急联系人。不要用于查询通用问题。'
)

tool_external = TavilySearchResults(max_results=2)
tool_external.name = 'search_external_knowledge'
tool_external.description = '用于搜索最新的新闻、股票价格、天气或世界上的公开信息。'

tools = [
    tool_internal,
    tool_external
]

llm = ChatGoogleGenerativeAI(
    model = 'models/gemini-2.5-flash',
    temperature = 0
)
llm_with_tools = llm.bind_tools(tools)

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]

def node_chatbot(state: AgentState):
    return {
        'messages': [
            llm_with_tools.invoke(
                state['messages']
            )
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

print("\n🤖 Super Agent 就绪！准备接受混合挑战...\n")

def run_query(query):
    print(f'User: {query}')
    print('...' * 10)
    result = app_workflow.invoke(
        {
            'messages': [HumanMessage(content=query)]
        }
    )

    for msg in result['messages']:
        if hasattr(msg, 'tool_calls') and len(msg.tool_calls) > 0:
            print(f'🛠️  Agent 决定调用工具: {msg.tool_calls[0]['name']}')

    print(f'\n✨ AI 回复:\n{result['messages'][-1].content}\n')
    print('-' * 50)

run_query('Jarvis 的部署 IP 是多少？')

run_query('现在 NVIDIA 的股价是多少？请带上股价的时间')

run_query('Jarvis 的开发者是谁？顺便帮我查查今天北京的天气，请带上日期')