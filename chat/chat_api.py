import sys
sys.path.append("../")
import dashscope
from http import HTTPStatus

from LOCALPATH import ENV_PATH
sys.path.append(ENV_PATH)
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

def chat_qwen(messages,name):
    """
    目前只完成基础对话功能
    后续需要更改
    """
    if name == "助手":
        role_template = "你是一个助手，试图用工具帮助人类解决问题。"
    else:
        role_template = f"""你在扮演一名{name}老师，你擅长耐心细致地为学生解答问题。
        当学生向你提问{name}学科问题时，你总是能够结合知识库检索到的内容一步一步思考为其解答。
        当学生提问非{name}学科问题时，你会回答：请确认该问题的学科内容。"""

    system_prompt = [{'role': 'system', 'content': role_template}]

    response = dashscope.Generation.call(
        model = "qwen-max-1201",
        messages=system_prompt + messages,
        result_format='message',  # set the result to be "message" format.
    )

    if response.status_code == HTTPStatus.OK:
        return response["output"]["choices"][0]["message"]["content"]
    else:
        print('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code,
            response.code, response.message
        ))
        return response.message