import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"

llm = ChatGoogleGenerativeAI(
    model = 'models/gemini-2.5-flash',
    temperature = 0
)

output_parser = StrOutputParser()

template_cmd = '''
你是一个 Linux 运维专家。
请直接给出完成以下任务所需的 shell 命令，尽量使用简洁的方式，不要包含任何解释或 markdown 格式。

操作系统: {os_type}
任务: {task}

命令:
'''
prompt_cmd = PromptTemplate.from_template(
    template=template_cmd
)
chain_cmd = (
    prompt_cmd | 
    llm | 
    output_parser
)

template_describe = '''
解释下这个命令: {command}
'''
prompt_describe = PromptTemplate.from_template(
    template=template_describe
)
chain_describe = (
    prompt_describe | 
    llm | 
    output_parser
)

chain_full = (
    RunnablePassthrough.assign(command = chain_cmd) |
    RunnablePassthrough.assign(explanation=chain_describe)
)

print(f"🚀 正在调用 LangChain 复合流水线...")
result = chain_full.invoke(
    {
        'os_type': 'k8s',
        'task': '查看占用 CPU 最高的 5 个pod'
    }
)


print("-" * 30)
print(f"💻 生成的命令: {result['command']}")
print("-" * 30)
print(f"🤖 命令解释: {result['explanation']}")