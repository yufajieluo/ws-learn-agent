import os
from langchain_google_genai import ChatGoogleGenerativeAI 
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"


template = '''
你是一个 Linux 运维专家。
请直接给出完成以下任务所需的 shell 命令，不要包含任何解释或 markdown 格式。

操作系统: {os_type}
任务: {task}

命令:
'''
prompt = PromptTemplate.from_template(
    template=template
)

llm = ChatGoogleGenerativeAI(
    model = 'models/gemini-2.5-flash',
    temperature = 0
)

output_parser = StrOutputParser()

template_describe = '''
解释下这个命令 {command}
'''
prompt_describe = PromptTemplate.from_template(
    template=template_describe
)

chain = prompt | llm | output_parser | prompt_describe | llm | output_parser

print(f"🚀 正在调用 LangChain 流水线...")
result = chain.invoke(
    {
        'os_type': 'k8s',
        'task': '查看占用 CPU 最高的 5 个pod'
    }
)

print(f'🤖 生成结果: {result}')