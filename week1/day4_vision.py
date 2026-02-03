
import os
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

model = genai.GenerativeModel(
    model_name="models/gemini-2.5-flash"
)

print("🤖 AI 正在观察图片并思考...")
prompt = "这张图片里有什么？请详细描述你看到的细节"
prompt = "这是一张 grafana 的监控面板截图，能否提取出现在可能出现的风险，以及可能的原因"
response = model.generate_content(
    [prompt, img],
    stream=True
)

print(" ------ 分析结果 -------")
for chunk in response:
    print(chunk.text, end = '', flush=True)