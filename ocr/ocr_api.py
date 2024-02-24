import os
import sys
import base64
import urllib
import requests

# .env path
sys.path.append("../..")

from dotenv import load_dotenv,find_dotenv
_ = load_dotenv(find_dotenv())

API_KEY = os.environ["OCR_API_KEY"]
SECRET_KEY = os.environ["OCR_SECRET_KEY"]

def get_file_content_as_base64(path, urlencoded=False):
    """
    获取base64编码
    :param path: 图像的byte
    :param urlencoded: 是否对结果进行urlencoded 
    :return: base64编码信息
    """
    # with open(path, "rb") as f:
    #     content = base64.b64encode(f.read()).decode("utf8")
    #     if urlencoded:
    #         content = urllib.parse.quote_plus(content)
    content = base64.b64encode(path).decode("utf8")
    if urlencoded:
        content = urllib.parse.quote_plus(content)
    return content


def get_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    return str(requests.post(url, params=params).json().get("access_token"))


def ocr(path,language_type="CHN_ENG",detect_direction=True,detect_language=True):

    language_type_config = "&language_type="+language_type
    detect_direction_config = "&detect_direction=true" if detect_direction else  "&detect_direction=false"
    detect_language_config = "&detect_language=true" if detect_language else  "&detect_language=false"
    url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token=" + get_access_token()
    payload="image=" + get_file_content_as_base64(path,True) + language_type_config + detect_direction_config + detect_language_config + "&probability=false"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    res = eval(response.text)["words_result"]
    return "\n".join([x["words"] for x in res])

if __name__ == "__main__":
    print(ocr("yuwen.png"))