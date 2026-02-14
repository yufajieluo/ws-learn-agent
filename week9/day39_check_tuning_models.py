import os
import google.generativeai as genai
from dotenv import load_dotenv

# 加载你的 API Key
load_dotenv()
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

print("🔍 正在查询支持微调的模型列表...\n")

count = 0
for m in genai.list_models():
    # 核心逻辑：检查该模型是否支持 'createTunedModel' 方法
    if "createTunedModel" in m.supported_generation_methods:
        print(f"✅ 模型名称: {m.name}")
        print(f"   显示名称: {m.display_name}")
        print(f"   输入限制: {m.input_token_limit}")
        print(f"   输出限制: {m.output_token_limit}")
        print("-" * 30)
        count += 1

if count == 0:
    print("❌ 未找到支持微调的模型（请检查 API Key 权限或区域）。")
else:
    print(f"\n✨ 共找到 {count} 个可微调的模型。")