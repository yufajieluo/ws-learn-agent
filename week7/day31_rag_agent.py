import os
import operator
from typing import Annotated, Literal, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.tools.retriever import create_retriever_tool
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

os.environ['GOOGLE_API_KEY'] = 'YOUR_GOOGLE_API_KEY'
PERSIST_DIR = './day30_chroma_db_data'

print('🔄 1. 正在加载昨天建立的向量数据库...')
embedding_function = GoogleGenerativeAIEmbeddings(
    model = 'models/gemini-embedding-001',
    task_type='retrieval_query'
)

vectorstore = Chroma(
    persist_directory=PERSIST_DIR,
    embedding_function=embedding_function
)

retriever = vectorstore.as_retriever(
    search_kwargs = {'k': 3}
)

tool_rag = create_retriever_tool(
    retriever=retriever,
    name='search_jarvis_internal_knowledge',
    description='当用户询问关于 AI 助手 "Jarvis" 的内部配置、IP地址、开发者或紧急联系人时，必须使用此工具查询。'
)

tools = [
    tool_rag
]

llm = ChatGoogleGenerativeAI(
    model='models/gemini-2.5-flash',
    temperature=0
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

node_tool = ToolNode(
    tools=tools
)

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

print("\n🤖 Agent 启动完毕！准备接受拷问...\n")
query1 = "Jarvis 部署在哪个服务器 IP？如果不响应找谁？"
print(f'User: {query1}')
result1 = app_workflow.invoke(
    {
        'messages': [HumanMessage(content=query1)]
    }
)
print(f'✨ AI 回复:')
print(result1['messages'][-1].content)
print(f'-' * 50)

query2 = "你好，请给我讲一个关于程序员的笑话。"
print(f"User: {query2}")
result2 = app_workflow.invoke(
    {"messages": [HumanMessage(content=query2)]}
)
print("✨ AI 回复:")
print(result2['messages'][-1].content)