
import os
import google.generativeai as genai

# set API key
os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"
genai.configure(
    api_key=os.environ["GOOGLE_API_KEY"],
    transport="rest"
)

# list available models
'''
print("🔍 正在获取你的 API Key 可用的模型列表...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ 模型名称: {m.name}")
except Exception as e:
    print(f"❌ 出错: {e}")
'''

generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "max_output_tokens": 4096
}

model = genai.GenerativeModel(
    model_name="models/gemini-2.5-flash", 
    generation_config=generation_config,
    system_instruction="你是一个资深的 Python 代码审查员。你的说话风格刻薄但一针见血。你只关心代码的性能和安全性， 并且你非常擅长 PUA 别人。另外，你更擅长使用中文"
    #system_instruction="你是一个非常有耐心的 Python 代码审查员。你的说话风格温和而富有建设性。你对待别人就像幼儿园老师一样。另外，你更擅长使用中文"
)

chat_session = model.start_chat(history=[])

user_input = """
def add(a, b):
    return a + b
"""

print(f"👤 用户代码: {user_input}")
print("🤖 Agent 正在思考...")

# send user input to the model
response = chat_session.send_message(user_input)

# print the model's response
print("-" * 50)
print(f"🤖 Agent 回复: {response.text}")
print("-" * 50)

#
print(f"📊 Token 消耗: {response.usage_metadata}")