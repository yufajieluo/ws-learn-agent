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

'''
class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name="gemini-pro-embedding-001"):
        self.model_name = model_name

    def embed_documents(self, texts):
        response = genai.embeddings.create(
            model=self.model_name,
            input=texts
        )
        return [embedding['embedding'] for embedding in response['data']]

    def embed_query(self, text):
        response = genai.embeddings.create(
            model=self.model_name,
            input=[text]
        )
        return response['data'][0]['embedding']
'''

class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        response = genai.embed_content(
            model="models/gemini-embedding-001",
            content=input,
            task_type='retrieval_document',
            title='DevOps_Runbook'
        )
        return response['embedding']

client = chromadb.Client()
collection = client.create_collection(
    name="devops_knowledge_base",
    embedding_function=GeminiEmbeddingFunction()
)

documents = [
    "错误码 503-A: 意味着 '网关过载'。临时解决方案是重启 Edge-Node-01 节点。",
    "错误码 503-B: 意味着 '后端数据库连接池满'。解决方案是扩容 RDS 实例。",
    "如果遇到 'Zombie Pod' (僵尸节点)，请不要手动删除，必须运行脚本 clean_zombies.sh。",
    "每周四下午 3 点是系统维护窗口，禁止任何发布操作。",
    "联系运维总监 '老王' 的紧急电话是 138-0000-8888，暗号是 '土豆哪里去挖'。",
]

ids = ["error_503a", "error_503b", "zombie_pod", "maintenance_window", "contact_info"]

print("📥 正在加载内部知识库...")
collection.add(
    documents=documents,
    ids=ids
)
print("✅ 知识库加载完成！")

def ask_jarvis(question: str, top_k: int = 2):
    print(f"👤 用户提问: {question}")
    results = collection.query(
        query_texts=[question],
        n_results=top_k
    )
    retrieved_docs = results['documents'][0]
    context_str = "\n".join(retrieved_docs)
    print(f"📚 [RAG] 搜到的参考资料:\n--- 开始 ---\n{context_str}\n--- 结束 ---\n")

    prompt = f"""
    你是一个专业的 DevOps 助手。请**仅根据**下面的参考资料回答用户的问题。
    如果参考资料里没有答案，就直接说“我不知道”，不要编造。

    参考资料：
    {context_str}

    用户问题：
    {question}
    """
    model = genai.GenerativeModel(
        model_name="models/gemini-2.5-flash",
    )
    response = model.generate_content(
        prompt,
    )
    return response.text

anwer1 = ask_jarvis('系统报了 503-A 错误，我该怎么办？')
print(f"🤖 Jarvis 回答: {anwer1}\n" + "="*50 + "\n")

answer2 = ask_jarvis("how I can contact the ops manager?")
print(f"🤖 Jarvis 回答:\n{answer2}\n" + "="*50 + "\n")

answer3 = ask_jarvis("食堂今天中午吃什么？")
print(f"🤖 Jarvis 回答:\n{answer3}\n" + "="*50 + "\n")