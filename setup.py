import streamlit as st
from ocr.paddleocr import ocr
from chat.chat_modelscope_agent import role


chat = role
# 设置头像
user_avatar = "./avatar/user_avatar.png"
bot_infos = {
    "助手":"./avatar/helper.png",
    "语文":"./avatar/chinese.png",
    "物理":"./avatar/physics.png",
    "化学":"./avatar/chemistry.png",
    # "数学":"./avatar/maths.png",
    # "英语":"./avatar/english.png",
    # "生物":"./avatar/biology.png",
}


# 程序运行机制说明:

# 每当操作某一个组件(例如输入一条消息按回车、选择另一个 bot)，
# 整个程序都会从头运行一遍，https://docs.streamlit.io/get-started/fundamentals/main-concepts
# 但st.session_state记录状态信息，不会被清空，https://docs.streamlit.io/library/api-reference/session-state


def create_all_bots():
    """
    创建“老师”角色-头像，初始化聊天界面
    """
    for name,avatar in bot_infos.items():
        st.toast(f"{name}老师上线!") # TLDR: 右下角弹出一个提醒消息，https://docs.streamlit.io/library/api-reference/status/st.toast
        st.session_state["history_bots"] = [name] + st.session_state["history_bots"]
        st.session_state["current_bot"] = name
        st.session_state["bot_avatar"][name] = avatar
        st.session_state["message"][name] = []
        

def on_current_bot_change():
    """
    切换当前对话的“老师”
    """
    st.session_state["current_bot"] = st.session_state.choose_bot


st.set_page_config(page_title="Teach-At", layout="wide", page_icon="🤖")



# st.session_state: {}
# 必须对后续要用到的 key 做初始化，否则会warning：https://docs.streamlit.io/library/api-reference/session-state
#    "history_bots" -> [bot name]
#    "current_bot" -> bot_name:string
#    "bot_avatar" -> dict: {key:bot_name, value: avatar_path}
#    "message" -> dict: {key:bot_name, value: [msg]}
#            msg是dict，key1是'role'，取值可能是user或者assistant
#            key2是'content'，是真正的消息

if "bot_avatar" not in st.session_state:
    st.session_state["bot_avatar"] = {}
if "message" not in st.session_state:
    st.session_state["message"] = {}
if "history_bots" not in st.session_state:
    st.session_state["history_bots"] = []
    create_all_bots()
if "current_bot" not in st.session_state:
    st.session_state["current_bot"] = None


with st.sidebar: # https://docs.streamlit.io/library/api-reference/layout/st.sidebar
    # st.title("聊天窗口")
    current_bot = st.radio("在线老师:", st.session_state["history_bots"], on_change=on_current_bot_change,key='choose_bot') 


slot1 = st.container(height=700, border=False)
with st.container(height=200):
    text_tab, img_tab = st.tabs(["发送消息","发送图片"])


# 遍历当前bot的历史消息，显示在聊天窗口，否则切换bot时历史消息看不到
for msg in st.session_state["message"][st.session_state["current_bot"]]:
    avatar = user_avatar
    if msg['role'] == 'assistant':
        avatar = st.session_state["bot_avatar"][st.session_state["current_bot"]]
    with slot1:
        # st.chat_message可理解为某一方(bot或user)发的消息容器，包括头像、消息内容
        with st.chat_message(msg["role"], avatar = avatar):
            if(isinstance(msg["content"], str)):
                st.markdown(msg["content"])
            else:
                for img in msg["content"]:
                    st.image(img)


# 发送图片
with img_tab:
    with st.form("img-form",clear_on_submit=True):
        uploaded_files = st.file_uploader("choose your images",accept_multiple_files=True,type=['jpg','png'])
        submitted = st.form_submit_button("UPLOAD!")
        if submitted and uploaded_files is not None:
            files_info = [] # 记录ocr信息
            for single_uploaded_file in uploaded_files:
                with slot1.chat_message("user",avatar = user_avatar):
                    image = st.image(single_uploaded_file) # 在聊天界面展示图片
                    files_info.append(ocr(single_uploaded_file.getvalue())) # ocr
            st.session_state["message"][st.session_state["current_bot"]].append({"role":"user","content":uploaded_files}) 
            with slot1:
                with st.chat_message("assistant",avatar=st.session_state["bot_avatar"][st.session_state["current_bot"]]):
                    with st.spinner("对方正在输入中......"):    
                        resp = chat("".join(files_info),st.session_state["current_bot"])
                        st.markdown(resp)
                        st.session_state["message"][st.session_state["current_bot"]].append({"role": "assistant", "content":resp})


if prompt := text_tab.chat_input():
    with slot1:
        with st.chat_message("user", avatar = user_avatar):
            st.markdown(prompt)
        st.session_state["message"][st.session_state["current_bot"]].append({"role": "user", "content": prompt})
        with st.chat_message("assistant",avatar=st.session_state["bot_avatar"][st.session_state["current_bot"]]):
            with st.spinner("对方正在输入中......"):    
                resp = chat(prompt,st.session_state["current_bot"])
                st.markdown(resp)
                st.session_state["message"][st.session_state["current_bot"]].append({"role": "assistant", "content":resp})