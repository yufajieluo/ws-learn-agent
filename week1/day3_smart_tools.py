
import os
import datetime
import google.generativeai as genai

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"
genai.configure(
    api_key=os.environ["GOOGLE_API_KEY"],
    transport="rest"
)

# =============================================
def get_pod_status(pod_name: str, namespace: str) -> dict:
    """
    查询指定 Kubernetes Pod 的状态

    args:
        pod_name: Pod 的名称
        namespace: Pod 所在的命名空间
    
    returns:
        包含 Pod 状态信息的字典，例如：
        {
            "status": "Running",
            "node": "node-1",
            "start_time": "2024-01-01T12:00:00Z"
        }
    """
    print(f"\n[系统日志] 🔍 正在调用工具 get_pod_status 查询 Pod {pod_name} 在命名空间 {namespace} 下的状态...")
    # 模拟返回数据
    if "db" in pod_name:
        mock_response = {
            "status": "Running",
            "node": "node-1",
            "start_time": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    else:
        mock_response = {
            "status": "CrashLoopBackOff",
            "node": None,
            "start_time": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    return mock_response

def get_exchange_rate(currency_from: str, currency_to: str) -> dict:
    """
    查询两种货币之间的实时汇率

    args:
        currency_from: 源货币代码，例如 "USD"
        currency_to: 目标货币代码，例如 "CNY"
    
    returns:
        包含汇率和日期的字典，例如：
        {
            "rate": 7.0,
            "date": "2024-01-01"
        }
    """
    print(f"\n[系统日志] 🔍 正在调用工具 get_exchange_rate 查询 {currency_from} 到 {currency_to} 的汇率...")
    mock_rates = {
        "USD-CNY": 7.25,
        "CNY-USD": 0.14,
        "USD-EUR": 0.92,
        "EUR-USD": 1.09
    }
    key = f"{currency_from.upper()}-{currency_to.upper()}"
    rate = mock_rates.get(key, None)
    if rate is None:
        response = { "rate": None, "date": datetime.datetime.now().strftime("%Y-%m-%d"), "status": "error", "msg": "不支持的货币对" }
    else:
        response = { "rate": rate, "date": datetime.datetime.now().strftime("%Y-%m-%d"), "status": "success" }

    return response


my_tools = [
    get_exchange_rate,
    get_pod_status
]

# =============================================

model = genai.GenerativeModel(
    model_name="models/gemini-2.5-flash", 
    tools=my_tools
)

chat_session = model.start_chat(
    history=[],
    enable_automatic_function_calling=True,
)

print("🤖 智能汇率助手已上线，准备为您服务！(输入 'quit' 退出)")
print("示例问题: '请告诉我当前 100 美元兑换成人民币是多少？'")

while True:
    user_input = input("\n👤 用户输入: ")
    if user_input.lower() == "quit":
        print("🤖 智能汇率助手已退出，期待下次为您服务！")
        break

    print("🤖 助手正在思考...")
    response = chat_session.send_message(user_input)

    print("-" * 50)
    print(f"🤖 助手回复: {response.text}")
    print("-" * 50)


print(f"-----------------------------------")
print(f"当前历史记录长度: {len(chat_session.history)} 条消息")
print(f"📊 Token 消耗: {response.usage_metadata}")