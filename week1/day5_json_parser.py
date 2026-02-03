import os
import json
import typing
import typing_extensions
import google.generativeai as genai

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"
genai.configure(
    api_key=os.environ["GOOGLE_API_KEY"],
    transport="rest"
)

class LogEntry(typing.TypedDict):
    timestamp: str
    service_name: str
    error_level: str
    error_message: str
    is_critical: bool
    suggested_action: str

model = genai.GenerativeModel(
    model_name='models/gemini-2.5-flash',
    generation_config={
        'response_mime_type': 'application/json',
        'response_schema': LogEntry
    }
)

raw_log = '''
[Incident Report]
时间是2026年1月23号下午2点半，我们的支付网关(payment-gateway)突然崩了。
日志显示 Connection refused，大概是因为数据库连接池满了。
目前生产环境已经断联，需要立即重启！
'''

print(f'-------- 原始输入 -------- \n{raw_log}\n')

response = model.generate_content(
    f'请提取这条日志的关键信息 {raw_log}'
)

try:
    log_data = json.loads(response.text)

    print(f'-------- 结构化输出(JSON) --------\n')
    print(json.dumps(log_data, indent=4, ensure_ascii=False))

    if log_data['is_critical']:
        print(f"\n🚨 [告警触发] 服务 {log_data['service_name']} 发生严重故障！")
        print(f"🛠 [自动执行] {log_data['suggested_action']}")
    else:
        print("\n✅ 这是一个普通日志，归档即可。")

except json.JSONDecodeError:
    print("❌ JSON 解析失败 (虽然用了 JSON 模式，但还是建议加 try-catch)")