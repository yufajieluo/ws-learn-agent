import os
import json
from dotenv import load_dotenv
from langsmith import evaluate
from langsmith.schemas import Run, Example
from langchain_google_genai import ChatGoogleGenerativeAI

from day37_langsmith import app

load_dotenv()

eval_llm = ChatGoogleGenerativeAI(
    model = 'models/gemini-2.5-flash'
)

def correctness_evaluator(run: Run, example: Example) -> dict:
    '''
    '''
    student_answer = run.outputs['messages'][-1].content
    ground_truth = example.outputs['ground_truth']
    question = example.inputs['question']

    prompt = f'''
    题目: {question}
    标准答案: {ground_truth}
    学生回答: {student_answer}
    
    请判断学生回答是否正确。如果意思一致，输出 "TRUE"，否则输出 "FALSE"。
    只输出 TRUE 或 FALSE，不要废话。
    '''
    grade = eval_llm.invoke(prompt).content.strip()

    return { 
        'key': 'accuracy',
        'score': 1 if grade == 'TRUE' else 0
    }

def target(inputs: dict):
    response = app.invoke(
        {
            'messages': [
                ('user', inputs['question'])
            ]
        },
        config = {
            'configurable': {
                'thread_id': 'eval_test'
            }
        }
    )
    return response

with open('week9/test_dataset.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

from langsmith import Client
client = Client()
dataset_name = 'Jarvis_Test_Set_V1'

if not client.has_dataset(dataset_name = dataset_name):
    ds = client.create_dataset(dataset_name=dataset_name)
    for item in data:
        client.create_example(
            inputs = {
                'question': item['question']
            },
            outputs = {
                'ground_truth': item['ground_truth']
            },
            dataset_id=ds.id
        )

print('🚀 开始自动化阅卷...')
evaluate(
    target,
    data = dataset_name,
    evaluators = [correctness_evaluator],
    experiment_prefix='v1-baseline'
)