
import os
import json
import uvicorn
import operator
from typing import TypedDict, Annotated, Optional, Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from langserve import add_routes

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from pydantic import BaseModel

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"

llm = ChatGoogleGenerativeAI(
    model='models/gemini-2.5-flash', 
    temperature=0.7
)

class MathState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    problem: str
    answer: Optional[str] = None
    answer_status: Optional[str] = None

class InputSchema(BaseModel):
    problem: str
    messages: list[BaseMessage] = []

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
        instructions = f"请做这个数学问题：{problem}. 请故意给出一个错误答案，不要解释。如果不是数学题，请调用 LLM 进行常规解答即可。"
    else:
        print(f"  🧑‍🎓 学生重新作答问题: {problem} （上次回答错误）")
        instructions = f'之前的回答不对。现在请认真计算 1+1，直接输出正确结果。如果不是数学题，请调用 LLM 进行常规解答即可。'
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

def router(state: MathState):
    status = state["answer_status"]
    if status == "correct":
        return 'end_path'
    else:
        return 'retry_path'
    
workflow = StateGraph(MathState)
workflow.add_node('student', node_student)
workflow.add_node('teacher', node_teacher)
workflow.set_entry_point('student')
workflow.add_edge('student', 'teacher')
workflow.add_conditional_edges(
    'teacher',
    router,
    {
        'end_path': END,
        'retry_path': 'student'
    }
)
memory = MemorySaver()

app_agent = workflow.compile(
    checkpointer=memory,
)
app_agent = app_agent.with_types(
    input_type=InputSchema
)


class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"

app = FastAPI(
    title="LangServe Agent API",
    version="1.0",
    #default_response_class=UTF8JSONResponse
)

#runnable_with_default = app_agent.with_config(
#    {"configurable": {"thread_id": "default_thread"}}
#)

@app.get('/', response_class=UTF8JSONResponse)
def read_root():
    response = {'message': '请访问 /math/playground 进行测试'}
    return response

@app.middleware("http")
async def log_raw_request(request: Request, call_next):
    # 只监控 /math/invoke 接口
    if request.url.path == "/math/invoke" and request.method == "POST":
        print("\n📨 [HTTP 监控] 收到请求！正在拆包检查...")
        
        # 偷看一下原始 Body (注意：读取后需要重置，否则后续流程会报错)
        body_bytes = await request.body()
        try:
            body_json = json.loads(body_bytes)
            print(f"📦 [HTTP Body]: {json.dumps(body_json, indent=2, ensure_ascii=False)}")
            
            # 重点检查 config 字段
            if "config" in body_json:
                print(f"✅ Body 里包含 config: {body_json['config']}")
            else:
                print("❌ Body 里竟然没有 config 字段！")
                
        except Exception as e:
            print(f"⚠️ 无法解析 Body JSON: {e}")

    # 继续处理请求
    response = await call_next(request)
    return response

async def per_req_config_modifier(config: Dict[str, Any], request: Any):
    if 'configurable' not in config:
        config['configurable'] = {}
    print(f'-------- {config}')
    body = await request.json()
    config_from_body = body.get("config", {}).get("configurable", {})
    current_thread_id = config_from_body.get("thread_id", "")
    print(f'-------- {current_thread_id}')
    config['configurable']['thread_id'] = current_thread_id
    
    return config

add_routes(
    app,
    app_agent,
    path='/math',
    per_req_config_modifier=per_req_config_modifier
)

if __name__ == "__main__":
    print('🚀 服务已启动！请访问: http://127.0.0.1:8001/math/playground')
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001
    )