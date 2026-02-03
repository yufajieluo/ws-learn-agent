
import os
import json
import time
import typing
import PIL.Image
import google.generativeai as genai

# configure API key
os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"
genai.configure(
    api_key=os.environ["GOOGLE_API_KEY"],
    transport="rest"
)

# simulated tool: fetch_service_logs
def fetch_service_logs(service_name: str) -> str:
    '''
    根据服务名称查询最近的服务器日志。
    Args:
        service_name: 具体的服务名称 (例如: payment-service, node-exporter, db-pod)
    Returns:
        最近的 3 行关键日志文本。
    '''
    print(f"\n[系统工具] 正在连接集群，抓取服务 '{service_name}' 的日志...")
    time.sleep(2)  # 模拟网络延迟

    if 'node' in service_name or 'exporter' in service_name:
        return 'ERROR: OutOfMemoryError - Java heap space\nWARNING: Garbage collection taking too long'
    elif 'db' in service_name:
        return 'FATAL: Connection limit exceeded (max: 100)\nERROR: Cannot accept new transaction'
    else:
        return f'INFO: Service {service_name} is healthy. Heartbeat OK.'

class IncidentReport(typing.TypedDict):
    incident_id: str
    service_affected: str
    detected_issue: str
    logs_evidence: str
    severity_level: typing.Literal['Critical', 'Warning', 'Info']
    action_plan: str

def submit_incident_report(report: IncidentReport) -> str:
    '''
    当调查结束时，必须调用此工具来提交最终报告。
    '''
    print("✅ [报告提交] 收到最终报告！") 
    return "Report received."    

tools_list = [
    fetch_service_logs,
    submit_incident_report
]

model = genai.GenerativeModel(
    model_name="models/gemini-2.5-flash",
    tools=tools_list
)

chat = model.start_chat(
    enable_automatic_function_calling=True
)

def run_investigation(image_path: str):
    print(f'---- 🕵️‍♂️ Jarvis-Ops 启动调查: {image_path} ---')

    if not os.path.exists(image_path):
        print(f"❌ 错误: 找不到图片 {image_path}，请先放一张图片在同级目录。")
        return

    img = PIL.Image.open(image_path)
    print(f"✅ 图片加载成功: {img.size} (宽x高)")

    print("🤖 AI 正在观察图片并进行故障分析...")
    prompt = '''
    系统指令：
    1. 你是故障排查专家和 DevOps 专家。
    2. 你会根据图片中的监控数据，判断可能出现的系统故障，并使用工具查询相关服务的日志以获取更多信息。
    3. 你必须先使用 `fetch_logs` 工具查询日志。
    4. 拿到日志后，你**必须**调用 `submit_incident_report` 工具来提交结果。
    5. **严禁** 直接输出自然语言文本，一切结果必须通过 `submit_incident_report` 提交。
    6. 【至关重要】在工具调用成功后，你必须向用户输出一个单词："DONE"，以结束任务。
    '''

    print("🤖 agent 启动...")
    response = chat.send_message(
        [prompt, img],
    )
    print(f"\n🤖 AI 最终回复: {response.text.strip()}")

    json_data = None
    for part in chat.history:
        #print(f'---- {part.parts[0].text}')
        if part.role == 'model' and part.parts[0].function_call:
            fc = part.parts[0].function_call
            if fc.name == 'submit_incident_report':
                print("\n🎁 === 捕获到结构化输出 (JSON) ===")
                if 'report' in fc.args:
                    json_data = fc.args['report']
                    # 兼容性处理：如果是 protobuf map，转 dict
                    if not isinstance(json_data, dict):
                        json_data = dict(json_data)
                break
    
    if json_data:
        print("✅ 成功拿到 JSON：")
        print(json.dumps(json_data, indent=4, ensure_ascii=False))
    else:
        print("❌ 未找到 JSON 数据")


run_investigation('test_image_4.png')