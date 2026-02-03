import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

st.set_page_config(
    page_title = '婷婷-Ops Chat',
    page_icon = '🤖'
)

with st.sidebar:
    api_key = st.text_input(
        'Google API Key',
        type = 'password'
    )
    if not api_key:
        api_key = os.getenv('GOOGLE_API_KEY')

if not api_key:
    st.warning('请在左侧输入 API Key 才能开始对话。')
    st.stop()

@st.cache_resource
def get_llm(api_key):
    genai = ChatGoogleGenerativeAI(
        model = 'models/gemini-2.5-flash',
        google_api_key = api_key,
        temperature = 0.7
    )
    return genai

llm = get_llm(api_key)

if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        AIMessage(
            content='我是婷婷，有什么可以帮您的？'
        )
    ]

for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message('user'):
            st.write(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message('assistant'):
            st.write(msg.content)

user_input = st.chat_input('输入你的问题...')

if user_input:
    with st.chat_message('user'):
        st.write(user_input)
    
    st.session_state.messages.append(
        HumanMessage(content=user_input)
    )

    with st.chat_message('assistant'):
        stream = True
        response_container = st.empty()
        full_response = ''

        chunks = llm.stream(st.session_state.messages)

        for chunk in chunks:
            full_response += chunk.content
            response_container.write(full_response + '▌')

        response_container.write(full_response)

    st.session_state.messages.append(
        AIMessage(content=full_response)
    )