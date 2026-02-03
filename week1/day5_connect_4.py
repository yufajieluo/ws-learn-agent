
import os
import json
import typing
import PIL.Image
import google.generativeai as genai

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"
genai.configure(
    api_key=os.environ["GOOGLE_API_KEY"],
    transport="rest"
)

image_path = 'test_image_4.png'

if not os.path.exists(image_path):
    print(f"❌ 错误: 找不到图片 {image_path}，请先放一张图片在同级目录。")
    exit()

img = PIL.Image.open(image_path)
print(f"✅ 图片加载成功: {img.size} (宽x高)")

class LogEntry(typing.TypedDict):
    timestamp: str
    instance_type: str
    instance_id: str
    status: str
    message: str
    root_cause: str
    suggested_action: str

model = genai.GenerativeModel(
    model_name="models/gemini-2.5-flash"
)

print("🤖 AI 正在观察图片并思考...")
prompt = "这张图片里有什么？请详细描述你看到的细节"
prompt = "这是一张 grafana 的监控面板截图，能否提取出现在可能出现的风险，以及可能的原因"
response = model.generate_content(
    [prompt, img],
    generation_config={
        'response_mime_type': 'application/json',
        'response_schema': list[LogEntry]
    }
)

try:
    log_data = json.loads(response.text)

    print(f'-------- 结构化输出(JSON) --------\n')
    print(json.dumps(log_data, indent=4, ensure_ascii=False))

except json.JSONDecodeError:
    print("❌ JSON 解析失败 (虽然用了 JSON 模式，但还是建议加 try-catch)")