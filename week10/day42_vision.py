import os
import PIL.Image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

image_path = 'test_image_1.png'

if not os.path.exists(image_path):
    print(f'❌ 找不到图片: {image_path}')
    print('请找一张图片放进去，例如截图或照片。')
    exit()

print(f"🖼️ 正在加载图片: {image_path} ...")
img = PIL.Image.open(image_path)

model = genai.GenerativeModel(
    model_name='models/gemini-2.5-flash'
)

print("🚀 正在发送给 AI ...")

prompt = "请详细描述这张图片里的内容。如果是界面，请解释各个元素的功能；如果是游戏，请告诉我这是什么游戏，主角在干什么。"

try:
    response = model.generate_content(
        [prompt, img]
    )
    print('-' * 50)
    print('🤖 AI 的视觉分析报告：')
    print(response.text)

except Exception as e:
    print(f'❌ 发生错误: {e}')