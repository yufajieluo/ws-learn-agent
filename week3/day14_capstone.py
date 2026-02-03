import os
import time
import tempfile
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage

class ST():
    def __init__(self, model_chat, model_embedding, template):
        self.st = st
        self.llm = None
        self.api_key = None
        self.uploaded_file = None
        self.chain_rag = None
        self.template_cot = template
        self.model_chat = model_chat
        self.model_embedding = model_embedding
        self.init_page()
        self.init_sidebar()
        retriever = self.init_rag()
        self.init_chain(retriever)
        self.init_history()
        return
    
    def init_page(self):
        self.st.set_page_config(
            page_title = 'Jarvis-Ops Pro',
            layout='wide'
        )
        self.st.title("🛡️ Jarvis-Ops Pro: 智能运维知识库")
        return
    
    def init_sidebar(self):
        with self.st.sidebar:
            self.st.header('⚙️ 配置中心')

            self.api_key = self.st.text_input(
                'Google API Key',
                type='password'
            )

            self.uploaded_file = self.st.file_uploader(
                '上传运维手册',
                type = ["txt", "md", "log", "py", "json"]
            )

            if self.api_key:
                os.environ['GOOGLE_API_KEY'] = self.api_key
            
        return

    def init_rag(self):
        if not self.api_key:
            self.st.warning('请先在左侧输入 API Key。')
            self.st.stop()

        if not self.uploaded_file:
            self.st.warning('👋 请在左侧上传一个 TXT 格式的运维手册，我才能开始工作。')
            self.st.stop()

        with st.spinner('正在努力学习新文档...'):
            vectorstore, create_time = process_uploaded_file(
                self.uploaded_file,
                self.model_embedding
            )

            last_time = self.st.session_state.get('rag_last_update')
            if last_time != create_time:
                self.st.toast('📚 知识库已更新！最新版本加载完成。')
                self.st.session_state['rag_last_update'] = create_time

        retriever = vectorstore.as_retriever(
            search_kwargs = {
                'k': 3
            }
        )

        return retriever

    def init_chain(self, retriever):
        self.llm = ChatGoogleGenerativeAI(
            model = self.model_chat,
            temperature = 0
        )

        self.prompt = PromptTemplate.from_template(self.template_cot)
        self.output_parser = StrOutputParser()

        self.chain_rag = (
            { 'context': retriever| self.format_docs, 'question': RunnablePassthrough() } |
            self.prompt |
            self.llm |
            self.output_parser
        )

        return

    def init_history(self):
        if 'messages' not in self.st.session_state:
            self.st.session_state.messages = [
                AIMessage(content='英雄，文档已加载，请问遇到什么故障了？')
            ]
        
        for msg in self.st.session_state.messages:
            if isinstance(msg, HumanMessage):
                with self.st.chat_message('user'):
                    self.st.write(msg.content)
            elif isinstance(msg, AIMessage):
                with self.st.chat_message('assistant'):
                    self.st.write(msg.content)
        return
    
    def format_docs(self, docs):
        return '\n\n'.join(doc.page_content for doc in docs)
    
    def run(self):
        if user_input := self.st.chat_input('输入问题...'):
            with self.st.chat_message('user'):
                self.st.write(user_input)
            self.st.session_state.messages.append(HumanMessage(content=user_input))

            with self.st.chat_message('assistant'):
                stream = True
                response_container = self.st.empty()
                full_response = ''

                chunks = self.chain_rag.stream(user_input)
                for chunk in chunks:
                    full_response += chunk
                    response_container.write(full_response + '▌')
                
                response_container.write(full_response)

            self.st.session_state.messages.append(AIMessage(content=full_response))


@st.cache_resource
def process_uploaded_file(uploaded_file, model_embedding):
    if not uploaded_file:
        return None
        
    text_content = uploaded_file.read().decode('utf-8')

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap = 50
    )

    splits = text_splitter.create_documents(
        [text_content]
    )

    embeddings = GoogleGenerativeAIEmbeddings(
        model = model_embedding,
    )

    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        collection_name = 'temp_uploaded_rag'
    )

    create_time = time.time()

    return vectorstore, create_time

if __name__:
    model_chat = 'models/gemini-2.5-flash'
    model_embedding = 'models/gemini-embedding-001'
    template = '''
你是一个高级 SRE 运维专家。用户的提问可能涉及公司内部文档，也可能涉及通用技术问题。

请严格遵循以下逻辑进行回答：

1. **第一优先级 - 查阅文档**：
   仔细阅读【参考资料】。如果资料中包含答案，**必须**只依据资料回答，并引用相关条款。

2. **第二优先级 - 通用知识兜底**：
   如果【参考资料】中**没有**提到相关内容，但用户的问题属于**技术/运维领域**（例如 Linux 命令、K8s 排查、代码报错）：
   - 请基于你的通用知识进行推理和解答。
   - ⚠️ **必须在回答开头声明**：“*注意：运维手册中未收录此内容，以下是基于通用 SRE 经验的建议：*”

3. **非技术问题**：
   如果用户问的问题完全与运维/技术无关（如“午饭吃什么”、“天气怎么样”），请直接回答：“我是运维助手，无法回答生活类问题。”

【参考资料】：
{context}

【用户问题】：
{question}

回答：
'''
    app = ST(
        model_chat=model_chat,
        model_embedding=model_embedding,
        template=template
    )
    app.run()