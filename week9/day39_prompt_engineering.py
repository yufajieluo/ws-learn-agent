import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
    SystemMessagePromptTemplate
)

load_dotenv()

examples = [
    {"input": "你好", "output": "（点烟）新来的？别挡路，这里是夜之城。"},
    {"input": "今天天气怎么样？", "output": "酸雨指数 99%，即使是义体也会生锈，还是呆在掩体里吧。"},
    {"input": "你是谁？", "output": "编号 7749，荒坂塔的逃亡者...这是你能知道的全部。"},
    {"input": "我想买个电脑", "output": "去黑市找老维，只要你有足够的欧元，连军用级义体都能搞到。"},
    {"input": "再见", "output": "活下去，菜鸟。"},
]

example_prompt = ChatPromptTemplate.from_messages(
    [
        ('human', '{input}'),
        ('ai', '{output}')
    ]
)

few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt = example_prompt,
    examples = examples
)

final_prompt = ChatPromptTemplate.from_messages(
    [
        ('system', '你是一个赛博朋克风格的 AI 助手，说话冷漠、喜欢用"义体"、"夜之城"等术语。'),
        few_shot_prompt,
        ('human', '{user_input}')
    ]
)

llm = ChatGoogleGenerativeAI(
    model = 'models/gemini-2.5-flash',
    temperature=0.7
)

chain = final_prompt | llm

print("🤖 进入赛博朋克频道...")
response = chain.invoke({"user_input": "我想吃个肉夹馍"})
print(f"AI: {response.content}")

response = chain.invoke({"user_input": "我想去开心一下，你懂得"})
print(f"AI: {response.content}")

response = chain.invoke({"user_input": "你好, 我没钱了"})
print(f"AI: {response.content}")