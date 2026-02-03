
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate
from langchain_core.output_parsers import StrOutputParser

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"

llm = ChatGoogleGenerativeAI(
    model = 'models/gemini-2.5-flash',
    temperature = 0
)

examples = [
    {
        "os": "Linux",
        "level": "High",
        "log": "OOM Killer invoked",
        "analysis": "Linux高危内存溢出。立即检查 dmesg，找出被杀死的进程，检查 swap 使用率。"
    },
    {
        "os": "Windows",
        "level": "Low",
        "log": "Update Service stopped",
        "analysis": "Windows低优服务停止。检查服务依赖，计划在维护窗口重启服务即可。"
    }
]

example_template = """
[历史案例]
系统: {os} | 等级: {level}
日志: {log}
AI处理: {analysis}
"""
prompt_example = PromptTemplate(
    template = example_template,
    input_variables = ['os', 'level', 'log', 'analysis']
)

few_shot_prompt = FewShotPromptTemplate(
    examples = examples,
    example_prompt = prompt_example,
    prefix = '你是一个智能运维助手。请模仿以下示例的思维方式回答问题：',
    suffix = """
[当前问题]
系统: {user_os} | 等级: {user_level}
日志: {user_log}
AI处理:""",
    input_variables = ["user_os", "user_level", "user_log"]
)

chain = few_shot_prompt | llm | StrOutputParser()

print("🚀 正在模仿示例进行推理...")
result = chain.invoke(
    {
        "user_os": "Kubernetes",
        "user_level": "Critical",
        "user_log": "Pod status CrashLoopBackOff, exit code 137"
    }
)
print(result)