import os
import operator
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"

class MathState(TypedDict):
    # 这里的 operator.add 至关重要，它保证了新消息是"追加"而不是"覆盖"
    messages: Annotated[list, operator.add]
    problem: str
    answer: str
    answer_status: str

llm = ChatGoogleGenerativeAI(
    model='models/gemini-2.5-flash', 
    temperature=0.7
)

def node_student(state: MathState):
    print("  🧑‍🎓 学生正在思考问题...")
    problem = state["problem"]
    messages = state['messages']

    is_retry = any(
        isinstance(msg, AIMessage) and "不正确" in msg.content 
        for msg in messages
    )

    if not is_retry:
        print(f"  🧑‍🎓 学生首次作答问题: {problem}")
        instructions = f"请做这个数学问题：{problem}. 请故意给出一个错误答案，不要解释。"
    else:
        print(f"  🧑‍🎓 学生重新作答问题: {problem} （上次回答错误）")
        #instructions = f"你上次的答案不正确。请重新做这个数学问题：{problem}. 请直接给出正确答案，不要解释。"
        instructions = f'之前的回答不对。现在请认真计算 1+1，直接输出正确结果。'
    response = llm.invoke(
        messages + [
            HumanMessage(
                content=instructions
            )
        ]
    )
    print(f"  🧑‍🎓 学生答案: {response.content}")
    
    return {
        "messages": [response],
    }

def node_teacher(state: MathState):
    print("  👩‍🏫 老师正在批改作业...")
    last_message = state["messages"][-1]
    student_answer = last_message.content

    judge_prompt = f'''
    你是一名严厉的数学老师。
    题目是：1 + 1 等于几？
    
    学生的回答是：【{student_answer}】
    
    请判断学生的回答是否在语义上正确。
    如果回答包含了错误答案（如 "等于3"），算错。
    
    请仅返回 JSON 格式结果，格式如下：
    {{"is_correct": true, "reason": "..."}}
    '''
    judge_response = llm.invoke([
        HumanMessage(content=judge_prompt)
    ])
    import json
    result_text = judge_response.content.replace("```json", "").replace("```", "")
    result = json.loads(result_text)

    if result.get("is_correct"):
        feedback = AIMessage(content="你的答案是正确的！")
        print(f"  ✅ 老师发现学生答案 {student_answer} 是正确的。")
        return {
            "answer_status": "correct",
            "messages": [feedback]
        }
    else:
        feedback = AIMessage(content="你的答案不正确，请再试一次。")
        print(f"  ❌ 老师发现学生答案 {student_answer} 不正确。")
        return {
            "answer_status": "incorrect",
            "messages": [feedback]
        }

    return {"messages": [AIMessage(content=feedback)]}

def router(state: MathState):
    status = state["answer_status"]
    if status == "correct":
        return 'end_path'
    else:
        return 'retry_path'

# --- 组装图 ---
workflow = StateGraph(MathState)
workflow.add_node("student", node_student)
workflow.add_node("teacher", node_teacher)
workflow.set_entry_point("student")
workflow.add_edge("student", "teacher")

workflow.add_conditional_edges(
    "teacher", 
    router,
    {
        'end_path': END,
        'retry_path': 'student'
    }
)

memory = MemorySaver()
thread_config = {"configurable": {"thread_id": "default_thread"}}

app = workflow.compile(
    checkpointer=memory,
    interrupt_before = ['teacher']
)


print('🚀 数学考试开始...')
inputs = {
    "messages": [], 
    "problem": "1 + 1 等于几？" 
}

app.invoke(
    inputs,
    config=thread_config
)

while True:
    print('------------------------------------')
    snapshot = app.get_state(thread_config)
    if not snapshot.next:
        print('🏁 流程已结束，退出循环。')
        break

    if snapshot.next[0] == 'teacher':
        current_content = snapshot.values["messages"][-1].content
        print(f"\n👨‍👩‍👧‍👦 家长查看当前答案: \n 【{current_content}】")
    
        new_content = input("\n⏸️ 家长是否进行修改答案(直接回车不改，输入文字修改): ")
        if new_content.strip():
            print("✍️ 家长正在修改答案...")
            app.update_state(
                thread_config,
                {"messages": [HumanMessage(content=new_content)]},
                as_node = 'student'
            )
            print("✅ 家长修改已保存到存档。")
        else:
            print("✅ 家长未修改答案，继续使用原答案。")

        print("▶️ 继续执行...")
        app.invoke(
            None,
            config=thread_config
        )
    else:
        app.invoke(
            None,
            config=thread_config
        )

snapshot = app.get_state(thread_config)
current_content = snapshot.values["messages"][-1].content
print(f"\n👨‍💼 最终提交的答案:\n【{current_content}】")

print('🏁 数学考试结束。')