from typing import TypedDict
from langgraph.graph import StateGraph, END

class MyState(TypedDict):
    message: str
    count: int


def node_uppercase(state: MyState):
    print(f"  🤖 [Node 1] 正在把 '{state['message']}' 变大写...")
    state["message"] = state["message"].upper()
    return state

def node_exclaim(state: MyState):
    print(f"  🤖 [Node 2] 正在给 '{state['message']}' 加感叹号...")
    state["message"] = state["message"] + "!"
    state["count"] += 1
    return state

def node_reverse(state: MyState):
    print(f"  🤖 [Node 3] 正在把 '{state['message']}' 反转...")
    state["message"] = state["message"][::-1]
    state["count"] += 1
    return state

workflow = StateGraph(MyState)
workflow.add_node("node_uppercase", node_uppercase)
workflow.add_node("node_exclaim", node_exclaim)
workflow.add_node("node_reverse", node_reverse)
#workflow.set_start("node_uppercase")
workflow.set_entry_point("node_uppercase")
workflow.add_edge("node_uppercase", "node_exclaim")
workflow.add_edge("node_exclaim", "node_reverse")
workflow.add_edge("node_reverse", END)

app = workflow.compile()

print("🚀 图流水线启动...")
initial_state: MyState = {
    "message": "hello, graph",
    "count": 0
}

result = app.invoke(initial_state)
print("\n🎉 最终结果:", result)