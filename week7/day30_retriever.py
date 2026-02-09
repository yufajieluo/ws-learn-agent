import os
import shutil
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

os.environ['GOOGLE_API_KEY'] = 'YOUR_GOOGLE_API_KEY'
PERSIST_DIR = './day30_chroma_db_data'

raw_text = """
【公司机密】关于 AI 助手 "Jarvis" 的内部配置手册 (2026版)
1. 核心代号：Jarvis-7。
2. 开发者：Wcy 大佬。
3. 部署服务器：阿里云 HK 节点，IP 192.168.0.7。
4. 紧急联系人：如果没有响应，请联系运维小张 (zhang@example.com)。
5. 报销政策：所有 API 调用费用由 "创新实验室" 承担，上限 $500/月。
"""

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 50,
    chunk_overlap = 10
)

docs = [
    Document(
        page_content = raw_text,
        metadata = {
            'source': 'internal_wiki'
        }
    )
]
splits = text_splitter.split_documents(docs)
print(f"✂️ 文档已切分为 {len(splits)} 个碎片。")

embedding_function = GoogleGenerativeAIEmbeddings(
    model = 'models/gemini-embedding-001',
    task_type = 'retrieval_document'
)

# if os.path.exists(PERSIST_DIR):
#     shutil.rmtree(PERSIST_DIR)

# print(f"💾 正在创建向量数据库并持久化到硬盘...")
# vectorstore = Chroma.from_documents(
#     documents = splits,
#     embedding = embedding_function,
#     persist_directory = PERSIST_DIR
# )
# print(f'✅ 数据库构建完成！')
vectorstore = Chroma(embedding_function = embedding_function, persist_directory = PERSIST_DIR)

retriever = vectorstore.as_retriever(
    search_type = 'similarity',
    search_kwargs = {'k':3}
)

query = '部署 IP 是多少？'
query = '如何联系紧急运维人员？'
print(f"\n❓ 提问: {query}")
retrieved_docs = retriever.invoke(query)

print(f"🔍 共检索到 {len(retrieved_docs)} 条相关信息：")
for i, doc in enumerate(retrieved_docs):
    print(f"\n📄 [结果 {i+1}]: {doc.page_content}")

print(f"📄 最终检索结果: {retrieved_docs[0].page_content}")
print(f"🏷️ 元数据: {retrieved_docs[0].metadata}")