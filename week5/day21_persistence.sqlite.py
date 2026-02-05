import os
import sqlite3
import operator
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
#from langgraph.checkpoint.memory import MemorySaver # 👈 1. 引入存档器
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"

llm = ChatGoogleGenerativeAI(model='models/gemini-2.0-flash', temperature=0.7)

class ChatState(TypedDict):
    # 这里的 operator.add 至关重要，它保证了新消息是"追加"而不是"覆盖"
    messages: Annotated[list, operator.add]

def call_model(state: ChatState):
    print("  🤖 Jarvis 正在思考...")
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

# --- 组装图 ---
workflow = StateGraph(ChatState)
workflow.add_node("model", call_model)
workflow.set_entry_point("model")
workflow.add_edge("model", END)

# 🔥 2. 初始化内存存档器
# MemorySaver 是把数据存在内存里（程序关掉就没了，适合测试）
# 生产环境通常用 PostgresSaver 或 SqliteSaver
# memory = MemorySaver()
with SqliteSaver.from_conn_string("day21_persistence.sqlite") as memory:
    app = workflow.compile(checkpointer=memory)

    # 🧵 线程配置：就像给这段对话起个名字叫 "session_1"
    config = {"configurable": {"thread_id": "session_1"}}

    # ----------- 1
    # print("\n🔴 [Round 1] 发送: 我是 WCY")
    # input_1 = {"messages": [HumanMessage(content="我叫 WCY，也是一名 AI 工程师。")]}

    # ----------- 2
    print("\n🔴 [Round 2] 发送: 你还记得我是谁吗？")
    input_1 = {"messages": [HumanMessage(content="你还记得我是谁吗？")]}
    output_1 = app.invoke(input_1, config=config)
    
    print(f"Jarvis: {output_1['messages'][-1].content}")

    print("\n✅ 程序运行结束。你可以把终端关掉，甚至重启电脑。")