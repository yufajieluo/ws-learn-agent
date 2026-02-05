import sqlite3
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage, AIMessage

class State(TypedDict):
    content: str
    feedback: str

def node_writer(state: State):
    print("  ✍️ [AI作家] 正在撰写文案...")
    draft = '''
战争使者艾莉亚·晨星在阿拉希盆地第一次见到他。
那是一个血色黄昏，她的长剑刺穿了一名兽人战士的肩膀，却在对上那双琥珀色眼眸时，手腕莫名一颤——那不是兽人常见的猩红狂怒，而是像迷失幼狼般的清澈困惑。
“为什么收手？”兽人按住流血的伤口，通用语带着粗砺口音。
艾莉亚这才惊醒，自己是暴风城第七军团最冷酷的指挥官，而他是部落的士兵。她本该斩下他的头颅。
“下一次不会。”她转身策马，银甲在落日下泛着冷光。
可她不知道，那个叫德拉卡什的年轻兽人，是第一次上战场——他原本是影月谷的星象学者，被迫拿起战斧。
'''
    return {
        "content": draft,
    }

def node_publisher(state: State):
    print(f"  📢 [AI发布员] 正在发布内容到全网...")
    print(f"  📄 最终发布内容: 【{state['content']}】")
    return {"feedback": "内容已成功发布，反响热烈！"}

workflow = StateGraph(State)
workflow.add_node("writer", node_writer)
workflow.add_node("publisher", node_publisher)
workflow.set_entry_point("writer")
workflow.add_edge("writer", "publisher")
workflow.add_edge("publisher", END)

conn = sqlite3.connect(
    "day22_human_interrupt.sqlite", 
    check_same_thread=False
)
memory = SqliteSaver(conn)

app = workflow.compile(
    checkpointer = memory,
    interrupt_before = ["publisher"]
)

thread_config = {"configurable": {"thread_id": "content_creation_1"}}

print("\n=== 🎬 阶段一：启动任务 ===")
app.invoke(
    None,
    config=thread_config
)

print("\n⏸️  系统已暂停。等待人类老板审批...")
print("(此时你可以去喝杯咖啡，程序状态已经保存在 sqlite 里了)")

print("\n=== 🎬 阶段二：老板来了 ===")

snapshot = app.get_state(thread_config)
current_content = snapshot.values["content"]
print(f"\n👨‍💼 老板查看当前内容:\n【{current_content}】")

new_content = input("👮‍♂️ 老板，你想修改草稿吗？(直接回车不改，输入文字修改): ")

if new_content.strip():
    print("✍️ 老板正在修改内容...")
    app.update_state(
        thread_config,
        {"content": new_content},
        as_node = 'writer'
    )
    snapshot = app.get_state(thread_config)
    current_content = snapshot.values["content"]
    print(f"\n👨‍💼 老板查看修改后的内容:\n【{current_content}】")
    print("✅ 修改已保存到存档。")
else:
    print("✅ 老板未修改内容，继续使用原稿。")


print("\n=== 🎬 阶段三：继续执行 ===")
app.invoke(
    None,
    config=thread_config
)

snapshot = app.get_state(thread_config)
current_content = snapshot.values["content"]
print(f"\n👨‍💼 最终发布的内容:\n【{current_content}】")

print("\n✅ 任务完成，程序结束。")
conn.close()