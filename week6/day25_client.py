import json
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8001/math/invoke"

st.set_page_config(
    page_title='数学考试客户端',
    page_icon='🧑‍🎓',
)
st.title('🤖 AI 数学补习班 (API 版)')
st.caption('前端: Streamlit | 后端: LangGraph + FastAPI')

with st.sidebar:
    st.header('🔧 设置')
    thread_id = st.text_input(
        '学号 (Thread ID)',
        value="student_001"
    )

    if st.button('🗑️ 清空对话历史'):
        st.session_state.messages = []
        st.success('✅ 对话历史已清空！')

if 'messages' not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    if msg['role'] == 'user':
        st.markdown(f"**👨‍🎓 学生:** {msg['content']}")
    else:
        st.markdown(f"**🤖 AI:** {msg['content']}")

if user_input := st.chat_input('请输入一道数学题 (例如: 1+1=?)'):
    with st.chat_message("user"):
        st.markdown(f"**👨‍🎓 学生:** {user_input}")
    st.session_state.messages.append(
        {'role': 'user', 'content': user_input}
    )

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown(f"**🤖 AI:** 正在思考...")

        try:
            payload = {
                'input': {
                    'problem': user_input,
                    'messages': [],
                    #'answer': None,
                    #'answer_status': None
                },
                'config': {
                    'configurable': {
                        'thread_id': thread_id
                    }
                },
                #'kwargs':{}
            }
            print(f"📤 发送请求到后端 API: {payload}")
            response = requests.post(API_URL, json=payload)

            if response.status_code == 200:
                result_json = response.json()

                all_messages = result_json['output']['messages']
                
                if len(all_messages) >= 2:
                    student_final_msg = all_messages[-2]['content']
                    teacher_final_msg = all_messages[-1]['content']
                    final_msg = f"学生最后回答: {student_final_msg}\n\n老师批改意见: {teacher_final_msg}"
                else:
                    final_msg = all_messages[-1]['content']

                message_placeholder.markdown(f"**🤖 AI:** {final_msg}")
                st.session_state.messages.append(
                    {'role': 'assistant', 'content': final_msg}
                )

                with st.expander("🔍 查看后端原始响应"):
                    st.json(result_json)
            else:
                message_placeholder.markdown(f"**🤖 AI:** 哎呀，出错了！状态码: {response.status_code}")
                st.text(f"错误详情: {response.text}")
        
        except Exception as e:
            message_placeholder.markdown(f"**🤖 AI:** 请求失败！")
            st.text(f"异常详情: {str(e)}")