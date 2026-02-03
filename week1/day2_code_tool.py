import os
import google.generativeai as genai

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"
genai.configure(
    api_key=os.environ["GOOGLE_API_KEY"],
    transport="rest"
)

generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "max_output_tokens": 4096
}

coder_instruction = """
你是一个 Python 代码优化专家。
规则：
1. 用户会输入一段 Python 代码。
2. 你只需要输出优化后的代码。
3. **严禁**输出任何 Markdown 标记（如 ```python）。
4. **严禁**输出任何解释性文字（如“这段代码优化了...”）。
5. 直接返回纯文本代码。
"""

model = genai.GenerativeModel(
    model_name="models/gemini-2.5-flash", 
    generation_config=generation_config,
    system_instruction=coder_instruction
)

chat_session = model.start_chat(history=[])

bad_code = """
def calc(a,b):
    res = 0
    for i in range(1):
        res = a + b
    return res
print(calc(1, 2))
"""

print(f"👤 用户代码: {bad_code}")
response = chat_session.send_message(bad_code)
print("-" * 50)
print(f"🤖 优化后代码: {response.text}")