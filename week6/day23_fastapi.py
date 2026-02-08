#! /usr/bin/env python3
# coding: utf-8

import os
import uvicorn
import operator
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, TypedDict, Annotated

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"

def mock_langgraph_agent(user_input: str, thread_id: str):
    print(f'🧠 [Agent] 正在思考 thread_id={thread_id} 的问题: {user_input}')
    if '1+1' in user_input:
        return '答案是 2 (来自 API)'
    else:
        return f'你说了: {user_input} (但我只会算 1+1)'

class UTF8JSONResponse(JSONResponse):
    media_type = 'application/json; charset=utf-8'

class ChatRequest(BaseModel):
    thread_id: str = 'default_thread'
    user_input: str

class ChatResponse(BaseModel):
    answer: str
    status: str

class MathState(TypedDict):
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

app = FastAPI(
    title="Math Agent API",
    version="1.0",
    default_response_class=UTF8JSONResponse
)

@app.get("/")
def read_root():
    response = {'message': '欢迎光临！这里的 AI 会做数学题哦！'}
    return response

@app.get('/health')
def read_health():
    return {'status': 'running'}

@app.get('/hello/{name}')
def read_hello(name: str):
    return {'message': f'你好，{name}！我是你的 AI 助手。'}

@app.post('/chat', response_model=ChatResponse)
def chat(request: ChatRequest):
    config = {
        'configurable': {
            'thread_id': request.thread_id,
        }
    }

    inputs = {
        'problem': [
            HumanMessage(content=request.user_input)
        ]
    }

    result = app_agent.invoke(
        inputs,
        config=config
    )

    final_msg = result['messages'][-1].content
    return {'answer': final_msg, 'status': 'success'}


if __name__ == "__main__":
    
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8000
    )