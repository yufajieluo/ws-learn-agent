import os
import time
#import google.generativeai as genai
from dotenv import load_dotenv

# set proxy
# os.environ["HTTP_PROXY"] = "http://127.0.0.1:7897"
# os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7897"
# os.environ["http_proxy"] = "http://127.0.0.1:7897"
# os.environ["https_proxy"] = "http://127.0.0.1:7897"
# os.environ['HTTP_PROXY'] = 'socks5://127.0.0.1:7897'
# os.environ['HTTPS_PROXY'] = 'socks5://127.0.0.1:7897'

import google.generativeai as genai

load_dotenv()
genai.configure(
    api_key=os.environ['GOOGLE_API_KEY']
)

def upload_to_gemini(path, mime_type = None):
    print(f'📤 正在上传文件: {path} ...')
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"✅ 上传成功: {file.display_name}")
    print(f"   文件 URI: {file.uri}")
    return file

def wait_for_files_active(files):
    print("⏳ 等待文件处理...", end="")
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == 'PROCESSING':
            print('.', end = '', flush = True)
            time.sleep(2)
            file = genai.get_file(name)
        if file.state.name != 'ACTIVE':
            raise Exception(f'❌ 文件处理失败: {file.state.name}')
    print(f'\n✅ 所有文件已就绪！')

pdf_path = '/home/wcy/Downloads/gpt-4.pdf'

if not os.path.exists(pdf_path):
    print(f'❌ 找不到文件: {pdf_path}，请检查路径！')
    exit()

pdf_file = upload_to_gemini(pdf_path, mime_type='application/pdf')
wait_for_files_active([pdf_file])

model = genai.GenerativeModel(
    model_name='models/gemini-2.5-flash',
    system_instruction='你是一位精通 AI 技术的学术研究员。你的任务是根据提供的 PDF 文档，极其精准地回答用户问题。如果文档没提到，就说不知道，不要编造。'
)

chat_session = model.start_chat(
    history=[
        {
            'role': 'user',
            'parts': [
                pdf_file,
                '请仔细阅读这份技术报告，通过分析图表和文字，准备回答我的问题。'
            ]
        }
    ]
)

print('-' * 30)
print('🤖 论文助手已就位！输入 "exit" 退出。')

while True:
    user_input = input('\nUser: ')
    if user_input.lower() in ['exit', 'quit']:
        break

    try:
        response = chat_session.send_message(user_input)
        print(f'AI: {response.text}')
        print(f'(Token 消耗: {response.usage_metadata.total_token_count})')
    except Exception as e:
        print(f'❌ 发生错误: {e}')