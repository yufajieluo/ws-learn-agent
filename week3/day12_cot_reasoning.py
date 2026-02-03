import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"

llm = ChatGoogleGenerativeAI(
    model = 'models/gemini-2.5-flash',
    temperature = 0
)

template = """
你是一个高级 SRE 工程师。面对用户的报错，请不要直接给出结论。
请遵循以下格式进行分析：

1. **现象分析**: 提取报错中的关键信息（时间、错误码、组件）。
2. **假设排查**: 列出 3 个可能的原因。
3. **推理验证**: 结合常识判断哪个原因可能性最大。
4. **最终建议**: 给出具体的修复步骤。

用户报错日志：
{error_log}

开始分析：
"""

prompt = PromptTemplate.from_template(
    template=template
)

chain = prompt | llm | StrOutputParser()

error_log = """
[Error] 2026-01-30 10:00:00 Connection to Redis (10.0.1.5:6379) failed.
TimeoutError: text-embedding-model timed out after 3000ms.
Context: High latency observed on node 'worker-04'. 
"""

print("🚀 正在进行深度推理...")
print("-" * 30)
result = chain.invoke(
    {
        'error_log': error_log
    }
)
print(result)