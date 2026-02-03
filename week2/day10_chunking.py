import os
import chromadb
import google.generativeai as genai
from chromadb import Documents, EmbeddingFunction, Embeddings

# set API key
os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"
genai.configure(
    api_key=os.environ["GOOGLE_API_KEY"],
    transport="rest"
)

def recursive_split_text(text, chunk_size=300, chunk_overlap=50):
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        if end >= text_length:
            chunks.append(text[start:])
            break

        found_split_point = False
        for i in range(end, start + chunk_overlap, -1):
            if text[i] in ['\n', '。', '！', '？', '.']:
                end = i + 1
                found_split_point = True
                break
        
        if not found_split_point:
            pass

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - chunk_overlap

        if start < 0:
            start = 0

    return chunks


long_runbook = """
=== 服务器运维终极手册 v2026 ===

第一章：基础环境检查
在遇到任何故障时，首先应检查服务器的基础指标。使用 `top` 命令查看 CPU 负载。
如果 load average 超过 CPU 核数的 2 倍，说明系统过载。
检查内存使用率，如果 free 内存极低且 swap 频繁交换，说明发生了内存泄漏。
此时应dump内存快照，并重启相关应用服务。

第二章：数据库常见故障
数据库连接超时 (Error 2002) 是最常见的问题。
这通常不是数据库本身挂了，而是防火墙拦截了连接。
请检查 iptables 或云厂商的安全组设置，确保 3306 端口对应用服务器 IP 开放。
如果出现 'Too many connections' 错误，说明连接池爆了。
这时候不要重启数据库！不要重启数据库！
应该先 kill 掉占着连接不干活的 sleep 线程，SQL 如下：
`select concat('KILL ',id,';') from information_schema.processlist where command='Sleep';`

第三章：老王的联系方式
如果上述方法都无效，且业务已瘫痪。
请立刻联系运维总监老王。
老王通常在三楼抽烟室。
如果找不到他，请拨打紧急热线 138-0000-8888。
切记，联系老王时不要说是谁让你打的。
"""

print("🔪 开始对长文档进行切片...")
chunks = recursive_split_text(
    long_runbook,
    chunk_size=100,
    chunk_overlap=20
)
print(f"✅ 切片完成！共切成 {len(chunks)} 块。\n")

for i, chunk in enumerate(chunks):
    print(f"--- [切片 {i+1}] (长度: {len(chunk)}) ---")
    print(chunk)
    print("-" * 30)

class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        response = genai.embed_content(
            model = "models/gemini-embedding-001",
            content = input,
            task_type='retrieval_document'
        )
        return response["embedding"]
        

client = chromadb.Client()
collection = client.create_collection(
    name = "chunked_knowledge",
    embedding_function=GeminiEmbeddingFunction()
)

metadatas = [
    {
        'source': 'devops_doc',
        'chunk_index': i,
        'doc_type': 'prod'
    } for i in range(len(chunks))
]

ids = [
    f'chunk_{i}' for i in range(len(chunks))
]
collection.add(
    documents=chunks,
    ids = ids,
    metadatas=metadatas
)

query = '数据库连接池满了怎么办？'
results = collection.query(
    query_texts = [query],
    n_results=1
)

print(f"\n🔍 用户提问: {query}")
print(f"📖 命中切片: {results['documents'][0][0]}")

current_index = results['metadatas'][0][0]['chunk_index']
window_size = 3
target_ids = []

total_chunks = len(chunks)
start_idx = max(0, current_index - window_size)
end_idx = min(total_chunks, current_index + window_size + 1)
for i in range(start_idx, end_idx):
    target_ids.append(f'chunk_{i}')

window_results = collection.get(
    ids = target_ids
)

final_context_parts = []
retrieved_docs_map = dict(
    zip(
        window_results['ids'],
        window_results['documents']
    )
)
for tid in target_ids:
    if tid in retrieved_docs_map:
        final_context_parts.append(retrieved_docs_map[tid])

full_context = "\n".join(final_context_parts)

print("-" * 30)
print("📚 [最终构建的完整上下文]:")
print(full_context)
print("-" * 30)

prompt = f"""
你是一个高级运维专家。请根据提供的上下文回答用户的问题。
注意：上下文可能包含不完整的句子，请综合前后文理解。

上下文：
{full_context}

用户问题：
{query}
"""

model = genai.GenerativeModel(
    model_name='models/gemini-2.5-flash'
)
response = model.generate_content(
    prompt
)
print(f"🤖 Jarvis 最终回复:\n{response.text}")