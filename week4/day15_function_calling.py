import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"

@tool
def get_current_time(location: str = 'China'):
    '''
    当用户询问当前时间、日期、现在几点了，或者询问特定地点的时间时，**必须**调用此工具。
    不要使用你自己的内部知识来回答时间问题。
    Args:
        location: 地点 (例如: China, US)
    '''
    import datetime
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f'现在 {location} 的时间是 {now}'

@tool
def calculate_power(base: float, exponent: float):
    '''
    计算数值的幂运算（base 的 exponent 次方）。
    AI 不擅长做精确数学计算，必须用这个工具。
    '''
    return base ** exponent


tools = [
    get_current_time,
    calculate_power
]

llm = ChatGoogleGenerativeAI(
    model = 'models/gemini-2.5-flash',
    temperature = 0
)

llm_with_tools = llm.bind_tools(tools=tools)

print('🤖 正在测试工具调用...')
query1 = '现在几点了？'
print(f'\n用户：{query1}')
result1 = llm_with_tools.invoke(query1)
print(f'AI 响应（Raw）：{result1.tool_calls}')

query2 = "计算 3.5 的 8 次方是多少？"
print(f"\n用户: {query2}")
result2 = llm_with_tools.invoke(query2)
print(f"AI 响应 (Raw): {result2.tool_calls}")

query3 = "你是谁？"
print(f"\n用户: {query3}")
result3 = llm_with_tools.invoke(query3)
print(f"AI 响应 (Content): {result3.content}")