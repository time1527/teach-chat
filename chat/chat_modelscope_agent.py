import sys
sys.path.append("../")

from LOCALPATH import ENV_PATH,REPO_PATH
sys.path.append(ENV_PATH)
sys.path.append(REPO_PATH)

from modelscope_agent.agents import RolePlay
from modelscope_agent.memory import MemoryWithRetrievalKnowledge,MemoryOnly
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())


from langchain_community.tools import ArxivQueryRun
from modelscope_agent.tools.langchain_proxy_tool import LangchainTool
from modelscope_agent.tools import TOOL_REGISTRY
TOOL_REGISTRY["arxiv"] = LangchainTool

NAME_DATA = {
    "语文":"chinese",
    "物理":"physics",
    "化学":"chemistry",
    "助手":"helper"
}


def role(prompt,name):
    """
    prompt：单次对话信息
        1.st.session_state记录展示在聊天页面的信息，
        如果使用st.session_state作为messages传入，
        需要每次遍历并对图片进行处理
        2.如果在setup.py中使用另一个类似st.session_state的dict记录string版本的对话内容，
        每次操作时会rerun，这时就没有了历史对话信息
        所以，需要借助memory

    name：“老师”名字，对应于st.session_state["current_bot"]
    """
    # 0.0：llm_config：通用
    llm_config = {
        'model': "qwen-max-1201", 
        'model_server': 'dashscope',
        }
    # 0.1：根据name获取存放memory的路径
    memory_history_path = REPO_PATH + "/history/" +  NAME_DATA[name]


    # 1：根据是否是“学科老师”区分使用的role_template、memory和function_list
    if name == "助手":
        # 2.0：template
        role_template = "你是一个助手，试图用工具帮助人类解决问题。"

        # 2.1：function_list
        function_list = [
            "wordart_texture_generation",
            {"arxiv":ArxivQueryRun()},
            "code_interpreter",
            # "text-translation-en2zh",
            # "text-translation-zh2en"
            ]

        # 2.2：初始化memory，并加载
        memory = MemoryOnly(memory_path = memory_history_path)
        history = memory.load_memory()

        # 3：初始化bot，根据prompt和history生成回复
        bot = RolePlay(function_list=function_list, llm=llm_config, instruction=role_template)
        response = bot.run(prompt,history = history,remote=False, print_info=True)
        # print(response)
    else:
        # 2.0：template
        role_template = f"""你在扮演一名{name}老师，你擅长耐心细致地为学生解答问题。
        当学生向你提问{name}学科问题时，你总是能够一步一步思考为其解答。
        当学生向你提问其他学科问题时，你只能回答：“请确认学科内容”。
        """

        # 2.1：function_list
        function_list = []

        # 2.2.0：获取vector_store的路径和其对应的index_name
        vs_storage_path = REPO_PATH + "/data/knowledge_vector_" + NAME_DATA[name]
        index_name = NAME_DATA[name]
        # 2.2.1：初始化memory（包括vector_store），并加载
        memory = MemoryWithRetrievalKnowledge(
            storage_path=vs_storage_path,
            name=index_name,
            memory_path=memory_history_path)
        history = memory.load_memory()

        # 2.3：根据prompt在vector_store中查找相关内容
        # TODO: 根据history和prompt进行查找
        ref_doc = memory.run(prompt,checked=True)

        # 3：初始化bot，根据prompt、history和ref_doc生成回复
        bot = RolePlay(function_list=function_list, llm=llm_config, instruction=role_template)
        response = bot.run(prompt,history = history, remote=False, print_info=True, ref_doc=ref_doc)

    text = ''
    for chunk in response:
        text += chunk

    # 4：更新并保存memory
    memory.update_history([{"role":"user","content":prompt},{"role":"assistant","content":text}])
    memory.save_memory()
    return text


# if __name__ == "__main__":
#     prompt = "arXiv:1706.03762v7 讲了什么"
#     name = "助手"
#     res = role(prompt,name)
#     print(res)