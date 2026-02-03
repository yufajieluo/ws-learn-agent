import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter

os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"

long_text = """
=== 运维手册 v2026 ===
1. 遇到 Error 500，请首先检查 Nginx 日志。
2. 如果数据库连接超时，请不要重启 DB，先检查防火墙 3306 端口。
3. 运维老王的电话是 138-0000-8888。
4. 周四是封网日，禁止发布。
"""

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 100,
    chunk_overlap = 20   
)

docs = text_splitter.create_documents(
    [long_text]
)

embeddings = GoogleGenerativeAIEmbeddings(
    model = 'models/gemini-embedding-001'
)

vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    collection_name='langchain_demo'
)

retriever = vectorstore.as_retriever(
    search_kwargs = {'k':1}
)

llm = ChatGoogleGenerativeAI(
    model = 'models/gemini-2.5-flash'
)

output_parser = StrOutputParser()

template = """
你是一个助手。请根据以下参考资料回答问题：

参考资料：
{context}

问题：{question}
"""
prompt = PromptTemplate.from_template(
    template=template
)

chain_rag = (
    { 'context': retriever,  'question': RunnablePassthrough() } |
    prompt |
    llm |
    output_parser
)

print("🚀 正在询问 LangChain RAG...")
result = chain_rag.invoke(
    '运维老王的电话是多少？'
)
print(f"🤖 回答: {result}")