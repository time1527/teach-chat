import sys
sys.path.append("../")
# debug start
# import sys
# sys.path.append("/home/dola/teach-chat")
# debug finish
import dashscope
from http import HTTPStatus
import json
from copy import deepcopy

from LOCALPATH import ENV_PATH,REPO_PATH
sys.path.append(ENV_PATH)
sys.path.append(REPO_PATH)

from modelscope_agent.memory import MemoryWithRetrievalKnowledge,MemoryOnly
from langchain_community.tools import ArxivQueryRun

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())


# used for function calling
ACTION_TOKEN = 'Action:'
ARGS_TOKEN = 'Action Input:'
OBSERVATION_TOKEN = 'Observation:'
ANSWER_TOKEN = 'Answer:'
TOOL_DESC_TEMPLATE = "{name}: {name} API。{description} 输入参数: {parameters} Format the arguments as a JSON object."
DEFAULT_EXEC_TEMPLATE = """\nObservation: <result>{exec_result}</result>\nAnswer:"""

# used for path
NAME_DATA = {
    "语文":"chinese",
    "物理":"physics",
    "化学":"chemistry",
    "助手":"helper"
}


def chat_qwen(prompt,name):
    """
    基本思路同chat_modelscope_agent.role
    2024/2/23：脱离modelscope-agent RolePlay的function调用————使用langchain的tool
    TODO: 脱离modelscope-agent的memory和rag
    """
    # 0：根据name获取存放memory的路径
    memory_history_path = REPO_PATH + "/history/" +  NAME_DATA[name]

    # 1. 根据“助手”/"老师"分流
    if name == "助手":
        # 2.0: role_template
        role_template = "你是一个助手，试图用工具帮助人类解决问题。"

        # 2.1：function_list
        arxiv = ArxivQueryRun()
        arxiv.name = "arxiv"
        function_list = [arxiv]
        
        # 2.2：tool_descs + tool_names + function_map 
        function_map = {}
        tool_descs = []
        for tool in function_list:
            parameters = []
            for name, arg in tool.args.items():
                tool_arg = deepcopy(arg)
                tool_arg['name'] = name
                tool_arg['required'] = True
                tool_arg['type'] = 'string'
                tool_arg.pop('title')
            parameters.append(tool_arg)
            tool_descs.append(TOOL_DESC_TEMPLATE.format(
                name=tool_arg['name'],
                description=tool_arg['description'],
                parameters=json.dumps(parameters, ensure_ascii=False)
                ))
            function_map[tool.name] = tool
        tool_descs = "\n\n".join(tool_descs)
        tool_names = ','.join(tool.name  for tool in function_list)

        # 2.3：初始化memory，并加载
        # 说明：该history不包含system prompt和其他罗里吧嗦的东西
        # 只有纯user输入和纯assistant输出
        memory = MemoryOnly(memory_path = memory_history_path)
        history = memory.load_memory()
        
        # 2.4：system prompt
        system_prompt = f"""
        # 工具

        ## 你拥有如下工具：

        {tool_descs}

        ## 当你需要调用工具时，请在你的回复中穿插如下的工具调用命令，可以根据需求调用零次或多次：

        工具调用
        Action: 工具的名称，必须是[{tool_names}]之一
        Action Input: 工具的输入
        Observation: <result>工具返回的结果</result>
        Answer: 根据Observation总结本次工具调用返回的结果，如果结果中出现url，请使用如下格式展示出来：![图片](url)

        # 指令

        {role_template}

        请注意：你具有图像和视频的展示能力，也具有运行代码的能力，不要在回复中说你做不到。
        """

        # 2.5：整理messages = system_prompt + 非system对话历史 + [query_prefix+prompt]
        # 2.4部分提到罗里吧嗦的东西指这里的query_prefix、之后解析llm输出部分
        messages = [{'role': 'system', 'content': system_prompt}]
        if history:
            assert history[-1]['role'] != 'user', 'The history should not include the latest user query.'
            if history[0]['role'] == 'system':
                history = history[1:]
            messages.extend(history)

        query_prefix = f"""
        {role_template}

        你可以使用工具：[{tool_names}]
        """
        messages.append({'role': 'user','content': "(" + query_prefix + ")" + prompt})


        # llm要根据tool的调用结果来再生成答案，所以这是一个循环
        # 其中inturn_prompt用来衔接 每次喂给llm的prompt————每次tool调用的输出
        max_try = 5
        inturn_prompt = ""
        while True and max_try > 0:
            max_try -= 1
            # 3：对话
            output = dashscope.Generation.call(
                model = "qwen-max",
                prompt = inturn_prompt,
                messages=messages,
                stop=['Observation:', 'Observation:\n'],
                )
            
            if output.status_code == HTTPStatus.OK:
                print(output.usage)  # The usage information
                llm_result = output.output["text"]  # The output text
            else:
                print(output.code)  # The error code.
                llm_result = output.message # The error message.
                break

            # 4.1：解析llm输出，判断是否调用工具
            text = llm_result
            print(f"at 第{5 - max_try}次尝试，llm输出：{text}")
            func_name, func_args = None, None
            i = text.rfind(ACTION_TOKEN)
            j = text.rfind(ARGS_TOKEN)
            k = text.rfind(OBSERVATION_TOKEN)
            if 0 <= i < j:  # If the text has `Action` and `Action input`,
                if k < j:  # but does not contain `Observation`,
                    # then it is likely that `Observation` is ommited by the LLM,
                    # because the output text may have discarded the stop word.
                    text = text.rstrip() + OBSERVATION_TOKEN  # Add it back.
                k = text.rfind(OBSERVATION_TOKEN)
                func_name = text[i + len(ACTION_TOKEN):j].strip()
                func_args = text[j + len(ARGS_TOKEN):k].strip()
                text = text[:k]  # Discard '\nObservation:'.
            
            # 4.2：调用工具
            if func_name != None:
                tool = function_map[func_name]
                params_json = json.loads(func_args)
                observation = tool.run(params_json)
                print(f"at 第{5 - max_try}次尝试，调用工具：{func_name},参数：{params_json}")
                format_observation = DEFAULT_EXEC_TEMPLATE.format(exec_result=observation)
                inturn_prompt += text + format_observation
            else:
                print(f"at 第{5 - max_try}次尝试，没有调用工具")
                inturn_prompt += text
                break
        final_response = llm_result

    else:
        # 2.0：template
        # 2.1：获取vector_store的路径和其对应的index_name
        vs_storage_path = REPO_PATH + "/data/knowledge_vector_" + NAME_DATA[name]
        index_name = NAME_DATA[name]

        # 2.2：初始化memory（包括vector_store），并加载
        memory = MemoryWithRetrievalKnowledge(
            storage_path=vs_storage_path,
            name=index_name,
            memory_path=memory_history_path)
        history = memory.load_memory()
        
        # 2.3：根据prompt在vector_store中查找相关内容
        # TODO: 根据history和prompt进行查找
        ref_doc = memory.run(prompt,checked=True)

        # 2.4：构建输入llm的messages
        system_prompt = f"""
        你是一名{name}老师，你擅长耐心细致地为学生解答问题。
        当学生向你提问{name}学科问题时，你总是能够一步一步思考并结合 知识库 为其解答。
        如果知识库内容和问题不相关，可以不参考知识库直接作答。
        当学生向你提问其他学科问题时，你只能回答：“请确认学科内容”。

        # 知识库

        {ref_doc}
        """

        query_prefix = f"""
        你是一名{name}老师，你擅长耐心细致地为学生解答问题。
        当学生向你提问{name}学科问题时，你总是能够一步一步思考并结合 知识库 为其解答。
        如果知识库内容和问题不相关，可以不参考知识库直接作答。
        当学生向你提问其他学科问题时，你只能回答：“请确认学科内容”。

        请查看前面的知识库
        """
        
        messages = [{'role': 'system', 'content': system_prompt}]
        if history:
            assert history[-1]['role'] != 'user', 'The history should not include the latest user query.'
            if history[0]['role'] == 'system':
                history = history[1:]
            messages.extend(history)

        messages.append({'role': 'user','content': "(" + query_prefix + ")" + prompt})
        
        # 3：调用llm
        output = dashscope.Generation.call(
            model = "qwen-max",
            messages=messages,
            )
        
        if output.status_code == HTTPStatus.OK:
            print(output.usage)  # The usage information
            final_response = output.output["text"]  # The output text
        else:
            print(output.code)  # The error code.
            final_response = output.message # The error message.
    

    memory.update_history([{"role":"user","content":prompt},{"role":"assistant","content":final_response}])
    memory.save_memory()
    return final_response

if __name__ == "__main__":
    ## function tools
    # prompt = "arXiv上1902.00751v2这篇论文讲了什么"
    # name = "助手"
    # res = chat_qwen(prompt,name)
    # print(res)
    # prompt = "刚刚那篇arXiv文章的题目是什么"
    # res = chat_qwen(prompt,name)
    # print(res)

    ## rag
    prompt = "你好"
    name = "化学"
    res = chat_qwen(prompt,name)
    print(res)

    prompt = "什么是还原反应"
    res = chat_qwen(prompt,name)
    print(res)