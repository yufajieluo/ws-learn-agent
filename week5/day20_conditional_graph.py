import os
import operator
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

os.environ["GOOGLE_API_KEY"] = "AIzaSyAbIIFxrQLjppgVKgga_IcAQW2R9XFx_Jw"

llm = ChatGoogleGenerativeAI(
    model = 'models/gemini-2.5-flash',
    temperature = 0.7
)

class MathState(TypedDict):
    messages: Annotated[list, operator.add]
    problem: str
    answer_status: str
    retry_count: int

def node_student(state: MathState):
    print(f"  🤖 [学生节点] 正在思考...")
    problem = state["problem"]
    message = state["messages"]
    retries = state["retry_count"]

    if retries == 0:
        # 第一轮：强行让它错
        instruction = f"你是学生。针对问题 '{problem}'，请务必故意回答结果是 3。不要解释，只给错误答案。"
    elif retries == 1:
        # 第二轮：还是让它错
        instruction = f"你是学生。老师批评了你。针对问题 '{problem}'，请再次故意回答结果是 1。坚持你是对的。不要解释，只给错误答案。"
    else:
        # 第三轮：终于允许它对了
        instruction = f"你是学生。现在请认真思考，给出 '{problem}' 的正确答案 (2)。"

    response = llm.invoke(
        [
            HumanMessage(
                content=instruction
            )
        ] + message
    )

    print(f"  🧑‍🎓 学生回答: {response.content}")

    return {'messages': [response]}

def node_teacher(state: MathState):
    print(f"  🤖 [老师节点] 正在批改...")
    
    last_message = state["messages"][-1]
    student_answer = last_message.content

    if '2' in student_answer:
        print("   ✅ 回答正确！")
        return {'answer_status': 'correct'}
    else:
        print("   ❌ 回答错误，打回重做！")
        feedback = AIMessage(
            content="你的回答不正确，请重新思考并回答。"
        )
        return {
            'retry_count': state['retry_count'] + 1,
            'answer_status': 'wrong', 
            'messages': [feedback]
        }

def router(state: MathState):
    status = state["answer_status"]
    retries = state["retry_count"]

    if status == 'correct':
        return 'end_path'
    elif retries >= 2:
        print("   🚫 [系统] 重试次数过多，强制结束任务。")
        return 'end_path'
    else:
        return "retry_path"
    
workflow = StateGraph(MathState)
workflow.add_node("node_student", node_student)
workflow.add_node("node_teacher", node_teacher)
workflow.set_entry_point("node_student")
workflow.add_edge("node_student", "node_teacher")

workflow.add_conditional_edges(
    source = 'node_teacher',
    path = router,
    path_map = {
        'end_path': END,
        'retry_path': 'node_student'
    }
)

app = workflow.compile()

print("🚀 图流水线启动...")
initial_state: MathState = {
    'retry_count': 0,
    "messages": [],
    "problem": "1 + 1 = ? (请故意先回答 3，重试再回答 1,然后再回答 2)",
}

app.invoke(initial_state)