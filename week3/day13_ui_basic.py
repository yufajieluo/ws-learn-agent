import time
import streamlit as st

st.title('🤖 Jarvis-Ops 控制台')

with st.sidebar:
    st.write('这是侧边栏配置区')
    temperature = st.slider(
        '模型温度',
        0.0,
        1.0,
        0.7
    )
    if st.button('清理缓存'):
        st.toast('缓存已清理')

st.write('### 欢迎回来，英雄。')

user_input = st.text_input(
    '请输入命令：',
    placeholder = '比如: 检查 K8s 状态'
)

if user_input:
    st.info(f'正在执行: {user_input} (Temperature: {temperature})')
    with st.spinner('AI 正在思考...'):
        time.sleep(2)
    st.success('执行完毕！')