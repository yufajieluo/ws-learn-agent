import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"

@tool
def get_current_time(location: str = 'China'):
    '''
    当用户询问时间时，必须调用此工具。
    '''
    import datetime
    print(f"    ⚙️ [系统日志] 正在连接时间服务器查询 {location}...")
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f'{location} 当前时间 {now}'

@tool
def calculate_power(base: float, exponent: float):
    '''
    当用户询问计算幂时，必须调用此工具。
    '''
    print(f"    ⚙️ [系统日志] 正在计算 {base} 的 {exponent} 次方...")
    return str(base ** exponent)

tools = [
    get_current_time,
    calculate_power
]

tools_map = {
    t.name: t for t in tools
}

llm = ChatGoogleGenerativeAI(
    model='models/gemini-2.5-flash',
    temperature=0
)
llm_with_tools = llm.bind_tools(tools)

def chat_with_tools(user_query: str):
    print(f"\n🔵 用户: {user_query}")

    messages = [HumanMessage(content=user_query)]
    ai_msg_1 = llm_with_tools.invoke(messages)

    messages.append(ai_msg_1)

    if ai_msg_1.tool_calls:
        print(f"🟡 AI (思考中): 我需要调用 {len(ai_msg_1.tool_calls)} 个工具...")
        for tool_call in ai_msg_1.tool_calls:
            tool_name = tool_call.get('name')
            tool_args = tool_call.get('args', {})
            tool_id = tool_call.get('id', '')

            if tool_name in tools_map:
                selected_tool = tools_map[tool_name]
                tool_result = selected_tool.invoke(tool_args)
                print(f"    ✅ [执行成功] {tool_name} -> 结果: {tool_result}")

                tool_msg = ToolMessage(
                    content = str(tool_result),
                    tool_call_id = tool_id,
                    name = tool_name
                )
                messages.append(tool_msg)
            else:
                print(f"    ❌ [错误] 找不到工具: {tool_name}")

        print("🟢 AI (最终回复): ", end="")
        ai_msg_final = llm_with_tools.invoke(messages)
        print(ai_msg_final.content)
    else:
        print(f"🟢 AI: {ai_msg_1.content}")

if __name__ == "__main__":
    chat_with_tools("请告诉我现在的时间。")
    chat_with_tools("请计算 5 的 3 次方是多少？")
    chat_with_tools("请计算 10 的 4 次方，并告诉我现在的时间。")
    chat_with_tools("你好！请问今天的日期是多少？")
    chat_with_tools("讲个地狱笑话给我听听。")