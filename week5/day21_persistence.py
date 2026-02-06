import os
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"

llm = ChatGoogleGenerativeAI(
    model = 'models/gemini-2.5-flash',
    temperature = 0.7
)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    
def call_model(state: ChatState):
    print(f'🤖 Jarvis 正在思考...')
    response = llm.invoke(state['messages'])
    return {'messages': [response]}

workflow = StateGraph(ChatState)
workflow.add_node('call_model', call_model)
workflow.set_entry_point('call_model')
workflow.add_edge('call_model', END)

memory = MemorySaver()
app = workflow.compile(
    checkpointer=memory
)

config = {
    'configurable': {
        'thread_id': 'session_1'
    }
}

print("\n=== 🔴 第一轮对话 (Thread ID: session_1) ===")
input_1 = {
    'messages': [
        HumanMessage(content="我叫 WCY，也是一名 AI 工程师。")
    ]
}
output_1 = app.invoke(
    input_1,
    config=config
)
print(f'Jarvis: {output_1['messages'][-1].content}')


print("\n=== 🟢 第二轮对话 (Thread ID: session_1) ===")
input_2 = {
    'messages': [
        HumanMessage(content="你还记得我是谁吗？")
    ]
}
output_2 = app.invoke(
    input_2,
    config=config
)
print(f'Jarvis: {output_2["messages"][-1].content}')

print("\n=== 🔵 第三轮对话 (Thread ID: session_2) ===")
config_new = {
    'configurable': {
        'thread_id': 'session_2'
    }
}
input_3 = {
    'messages': [
        HumanMessage(content="还记得我叫什么名字吗？")
    ]
}
output_3 = app.invoke(
    input_3,
    config=config_new
)
print(f'Jarvis: {output_3["messages"][-1].content}')