import streamlit as st
from langserve import RemoteRunnable
from langchain_core.messages import HumanMessage

st.set_page_config(
    page_title='数学考试客户端',
    page_icon='🧑‍🎓',
)
st.title('📡 AI 数学考试 (流式直播版)')
st.caption('前端: RemoteRunnable | 后端: LangGraph Stream')

API_URL = "http://127.0.0.1:8001/math/"

with st.sidebar:
    st.header('🔧 设置')
    thread_id = st.text_input(
        '学号 (Thread ID)',
        value="student_001",
        key='tid'
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
        status_container = st.status("🚀 AI 正在启动...", expanded=True)
        final_answer_placeholder = st.empty()

        try:
            remote_agent = RemoteRunnable(API_URL)
            inputs = {
                'problem': user_input,
                'messages': []
            }
            config = {
                'configurable': {
                    'thread_id': thread_id
                }
            }
            final_text = ''

            for chunk in remote_agent.stream(
                input=inputs,
                config=config
            ):
                if 'student' in chunk:
                    student_msg = chunk['student']['messages'][0].content
                    status_container.markdown(f"🧑‍🎓 **学生作答**: {student_msg}")
                elif 'teacher' in chunk:
                    teacher_res = chunk['teacher']
                    teacher_msg = chunk['teacher']['messages'][0].content
                    status = teacher_res.get('answer_status', 'unknown')
                    #status_container.markdown(f"👨‍🏫 **老师反馈**: {teacher_msg}")
                    if status == 'correct':
                        status_container.success(f"👩‍🏫 **老师判卷**: {teacher_msg} (通过)")
                        final_text = f'✅ 最终结果: {teacher_msg}'
                    elif status == 'incorrect':
                        status_container.error(f"👩‍🏫 **老师判卷**: {teacher_msg} (打回重做)")
            
            status_container.update(
                label = f'✨ 考试结束',
                state = 'complete',
                expanded=False
            )

            if final_text:
                final_answer_placeholder.markdown(f"**🤖 AI:** {final_text}")
                st.session_state.messages.append(
                    {'role': 'assistant', 'content': final_text}
                )
            else:
                final_answer_placeholder.markdown(f"**🤖 AI:** 考试结束，但未收到老师反馈。")
                st.session_state.messages.append(
                    {'role': 'assistant', 'content': "考试结束，但未收到老师反馈。"}
                )

        except Exception as e:
            status_container.error(f"❌ 请求出错: {str(e)}")
            st.session_state.messages.append(
                {'role': 'assistant', 'content': f"请求出错: {str(e)}"}
            )