import os
import PIL.Image
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

image_path = 'receipt.jpg'

if not os.path.exists(image_path):
    print(f"❌ 找不到图片: {image_path}")
    print("请找一张发票或小票的照片放进去。")
    exit()

img = PIL.Image.open(image_path)
print(f"🧾 已加载票据: {image_path}")

model = genai.GenerativeModel(
    model_name='models/gemini-2.5-flash',
    generation_config={
        'response_mime_type': 'application/json'
    }
)

prompt = '''
提取这张票据里的关键信息。
请严格按照以下 JSON 格式输出，不要包含任何 Markdown 标记或额外文字：

{
  "store_name": "商店名称 (string)",
  "date": "交易日期 (YYYY-MM-DD)",
  "total_amount": "总金额 (number)",
  "currency": "货币单位 (string, e.g. USD, CNY)",
  "items": [
    {
      "name": "商品名称",
      "price": "单价 (number)",
      "quantity": "数量 (number)"
    }
  ]
}

如果有看不清的字段，请填 null。
'''

print("🚀 正在提取数据 (这比传统 OCR 强在它能理解语义)...")

try:
    response = model.generate_content([prompt, img])

    data = json.loads(response.text)

    print('-' * 50)
    print("🚀 正在提取数据 (这比传统 OCR 强在它能理解语义)...")
    print(json.dumps(data, indent=2, ensure_ascii= False))

    print("-" * 30)
    # 模拟业务逻辑：直接读取字段
    print(f"🏠 店铺: {data.get('store_name')}")
    print(f"💰 总计: {data.get('total_amount')} {data.get('currency')}")
    print(f"🛒 买了 {len(data.get('items', []))} 件商品")

except Exception as e:
    print(f"❌ 发生错误: {e}")
    # 如果报错，打印原始文本看看 AI 到底回了什么
    if 'response' in locals() and response.text:
        print(f"AI 原始回复: {response.text}")