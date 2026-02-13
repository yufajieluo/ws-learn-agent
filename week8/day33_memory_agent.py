import os
import operator
import sqlite3
import requests
import urllib3
from typing import Annotated, Literal, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import Tool
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain.tools.retriever import create_retriever_tool

os.environ['GOOGLE_API_KEY'] = 'GOOGLE_API_KEY'
os.environ['TAVILY_API_KEY'] = 'TAVILY_API_KEY'

PERSIST_DIR = 'day30_chroma_db_data'
DB_PATH = 'agent_memory.sqlite'

embedding_function = GoogleGenerativeAIEmbeddings(
    model = 'models/gemini-embedding-001',
    task_type = 'retrieval_query'
)

vectorstore = Chroma(
    persist_directory=PERSIST_DIR,
    embedding_function=embedding_function
)

retriever = vectorstore.as_retriever(
    search_kwargs = {'k': 3}
)

tool_internal = create_retriever_tool(
    retriever=retriever,
    name = 'search_internal_knowledge',
    description='【绝密】仅用于查询公司内部 AI 助手 "Jarvis" 的配置、IP地址、开发者或紧急联系人。'
)

tool_external = TavilySearchResults(max_results=2)
tool_external.name  = 'search_external_knowledge'

tools = [
    tool_internal,
    tool_external
]

llm = ChatGoogleGenerativeAI(
    model = 'models/gemini-2.5-flash',
    temperature=0
)
llm_with_tools = llm.bind_tools(tools)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]

def node_chatbot(state: AgentState):
    return {
        'messages': [
            llm_with_tools.invoke(state['messages'])
        ]
    }

node_tool = ToolNode(tools = tools)

def should_continue(state: AgentState) -> Literal['tools', '__end__']:
    last_messages = state['messages'][-1]
    if last_messages.tool_calls:
        return 'tools'
    else:
        return '__end__'

workflow = StateGraph(AgentState)
workflow.add_node('agent', node_chatbot)
workflow.add_node('tools', node_tool)
workflow.set_entry_point('agent')
workflow.add_conditional_edges('agent', should_continue)
workflow.add_edge('tools', 'agent')

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
memory = SqliteSaver(conn)

app_workflow = workflow.compile(checkpointer=memory)

print("✅ 带记忆的 Super Agent 已就绪！")

def chat_loop():
    print("\n💡 提示：输入 'exit' 退出，输入 'switch' 切换会话 ID")

    thread_id = input('请输入当前会话 ID (例如 user_1):') or 'user_1'

    while True:
        user_input = input(f'\n[{thread_id}] User: ')

        if user_input.lower() == 'exit':
            break

        if user_input.lower() == 'switch':
            thread_id = input('请输入新的会话 ID: ')
            print(f'🔄 已切换到会话: {thread_id}')
            continue

        config = {'configurable': {'thread_id': thread_id}}

        print("✨ AI: ", end="", flush=True)

        events = app_workflow.stream(
            {'messages': [HumanMessage(content = user_input)]},
            config = config,
            stream_mode = 'values'
        )

        for event in events:
            if 'messages' in event:
                last_msg = event['messages'][-1]
                if isinstance(last_msg, BaseMessage) and last_msg.type == 'ai' and not last_msg.tool_calls:
                    print(last_msg.content, end = '', flush = True)

        print()

if __name__ == '__main__':
    chat_loop()