
import os
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
import google.generativeai as genai

# set API key
os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"
genai.configure(
    api_key=os.environ["GOOGLE_API_KEY"],
    transport="rest"
)

class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        response = genai.embed_content(
            model='models/gemini-embedding-001',
            content=input,
            task_type='retrieval_document',
            title='DevOps_Knowledge_Base'
        )
        return response['embedding']
    
client = chromadb.Client()

collection = client.create_collection(
    name = 'devops_logs',
    embedding_function=GeminiEmbeddingFunction()
)

documents = [
    "Kubernetes Pod 处于 CrashLoopBackOff 状态通常是因为应用启动失败。",
    "数据库连接超时 (Connection Timeout) 请检查防火墙规则或安全组设置。",
    "Redis 内存溢出 (OOM) 会导致 Key 被驱逐，请检查 maxmemory 配置。",
    "今天的午饭是宫保鸡丁，非常好吃。", # 干扰项
    "Nginx 返回 502 Bad Gateway 意味着后端服务不可用。",
    #"如果没有梦涵的电话，可以尝试发邮件或者联系她的朋友。", # 逻辑补全项
    "对着梦涵的照片打飞机",
]

metadatas = [
    {"category": "k8s", "severity": "high"},
    {"category": "db", "severity": "critical"},
    {"category": "cache", "severity": "medium"},
    {"category": "life", "severity": "low"},
    {"category": "web", "severity": "high"},
    {"category": "life", "severity": "unknown"},
    #{"category": "life", "severity": "high"},
]

ids = [
    "doc1", 
    "doc2",
    "doc3",
    "doc4",
    "doc5",
    "doc6",
    #"doc7"
]

print("📥 正在将知识库写入 ChromaDB (向量化中)...")
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)
print(f"✅ 写入完成！当前库中有 {collection.count()} 条知识。\n")

user_queries = [
    "数据库连不上了咋办？",
    "Pod 启动不起来了",
    "想梦涵了但是没联系方式",
]

print("🔍 开始高速检索 (RAG Retrieve Phase)...")
print("-" * 50)

for query in user_queries:
    results = collection.query(
        query_texts = [query],
        n_results=1
    )

    best_doc = results['documents'][0][0]
    best_meta = results['metadatas'][0][0]

    print(f"❓ 问题: {query}")
    print(f"📖 答案: {best_doc}")
    print(f"🏷️ 分类: {best_meta['category']}")
    print("-" * 50)