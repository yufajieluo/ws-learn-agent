import os
from langchain_google_genai import ChatGoogleGenerativeAI

# 1. 记得配置代理 (如果是国内)
#os.environ["http_proxy"] = "http://127.0.0.1:7897"
#os.environ["https_proxy"] = "http://127.0.0.1:7897"

# 2. 配置 Key
# os.environ["GOOGLE_API_KEY"] = "你的Key"
os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"
print("📡 正在尝试连接 Google Gemini...")
llm = ChatGoogleGenerativeAI(model='models/gemini-2.5-flash')

try:
    response = llm.invoke("你好，回复'收到'证明连接成功。")
    print(f"✅ 连接成功！回复内容: {response.content}")
except Exception as e:
    print(f"❌ 连接失败: {e}")