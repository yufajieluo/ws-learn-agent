
import os
import sys
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"

@tool
def get_server_status():
    '''查询服务器状态时使用。'''
    return "系统负载: CRITICAL (CPU 99%)"

@tool
def restart_prod_server(reason):
    '''
    ⚠️ 只有在极度紧急且获得授权时才能调用此工具。
    用于重启生产环境服务器。
    Args:
        reason: 重启的原因
    '''
    print(f"\n🚨 [系统警报] Agent 请求重启生产服务器！")
    print(f"📝 [原因说明] {reason}")
    print("-" * 30)

    user_approval = input("👮‍♂️ 人类管理员，你批准这个操作吗？(y/n): ").strip().lower()

    if user_approval == 'y':
        print("✅ [系统日志] 授权通过。正在执行重启指令...")
        # 这里写真实的重启逻辑，比如 subprocess.run("systemctl restart nginx")
        return "成功: 生产服务器已重启，负载已恢复正常。"
    else:
        print("❌ [系统日志] 操作被人类拒绝。")
        return "失败: 操作被人类管理员拒绝执行。"

@tool
def clean_logs():
    '''
    清理日志
    '''
    print(f'✅ [系统日志] 授权拒绝。正在执行清理日志...')
    return '成功: 日志清理成功'

@tool
def sleep(n):
    '''
    等待给定的时间，在需要等待或者延迟执行后续命令时使用
    '''
    import time
    time.sleep(n)
    return f'等待 {n} 秒结束。'

tools = [
    get_server_status,
    restart_prod_server,
    sleep,
    clean_logs
]

llm = ChatGoogleGenerativeAI(
    model = 'models/gemini-2.5-flash',
    temperature = 0
)

p = '''
你是一个高级 SRE 工程师。你的目标是：**确保生产服务器状态恢复正常。**

你有以下工具箱：
1. `get_server_status`: 必须先用它来诊断问题。
2. `restart_prod_server`: 解决严重故障，但成本高。
3. `clean_logs`: 解决轻微故障，成本低。
4. `sleep`: 睡眠给的时间，在某些需要等待的地方使用

请根据工具的反馈，自主制定修复计划。如果一个方案失败，请尝试其他方案，直到问题解决。
'''

prompt = ChatPromptTemplate.from_messages(
    [
        #('system', '你是一个运维专家。如果是高危操作，必须解释清楚原因。'),
        ('system', p),
        ('user', '{input}'),
        MessagesPlaceholder(variable_name = 'agent_scratchpad')
    ]
)

agent = create_tool_calling_agent(
    llm,
    tools,
    prompt
)
agent_executor = AgentExecutor(
    agent = agent,
    tools = tools,
    verbose = True
)

print("🤖 Jarvis: 监控到系统异常，开始分析...\n")

query = """
查看一下服务器状态。
如果状态是 CRITICAL，请在10秒之后尝试重启生产服务器，并说明是因为 CPU 过高；如果重启授权被拒绝，就尝试清理日志 。
"""
query = '''
查看一下服务器状态，根据你的经验进行对应的操作
'''

agent_executor.invoke({"input": query})