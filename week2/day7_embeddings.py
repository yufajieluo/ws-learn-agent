
import os
import numpy as np
import google.generativeai as genai

# set API key
os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"
genai.configure(
    api_key=os.environ["GOOGLE_API_KEY"],
    transport="rest"
)

def get_doc_embedding(text):
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_document",
        #title=''
    )
    return result['embedding']

def get_query_embedding(text):
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_query"
    )
    return result['embedding']

user_input = "数据库连接失败怎么办？"
user_input = "How to fix database connection failure?"
user_input = "我想梦涵了怎么办？但是我没有她的电话。"

documents = [
    '今天的午饭很好吃',
    'Kubernetes Pod 处于 CrashLoop。',
    '检查防火墙端口和数据库账号密码。',
    'please check the firewall ports and database credentials',
    '给梦涵打电话告诉她我想她了',
    '对着梦涵的照片打飞机',
]

print(f'👤 用户问题: {user_input}\n')

query_vec = get_query_embedding(user_input)
#print(f'🔍 用户问题的嵌入向量: {query_vec}\n')

for doc in documents:
    doc_vec = get_doc_embedding(doc)
    #similarity = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec))
    similarity = np.dot(query_vec, doc_vec)
    print(f'📄 文档: {doc}\n   相似度: {similarity:.4f}\n')

    if similarity > 0.7:
        print(f'✅ 找到相关文档: {doc}\n')

    print('-' * 50)
print("🔍 嵌入向量比较完成。")