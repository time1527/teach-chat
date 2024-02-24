# teach-chat

## 介绍

基于modelscope-agent实现的类家教对话场景：

1. 知识库：各科目可以内嵌知识库，例如教材
2. 记忆：对话时，“实时”加载、更新保存对话内容
   1. `history`：

      1. 在关闭前端后，也可以在 `history`文件夹看到历史对话
      2. `run.sh`默认在启动前端之前删除历史对话，可通过简单修改继续本次之前的对话
   2. `streamlit`：

      1. 前端只支持本次（即打开网页）的聊天内容显示
      2. 前端可任意切换对话角色，例如：可和“助手”聊天后去咨询“化学老师”问题，咨询完之后可继续返回“助手”聊天框，和“助手”的历史聊天内容仍在相应聊天框内可见
      3. 不支持在对方未输出回答前切换对话对象：对方的输出内容不会出现在前端，但实际 `history`中会保存
3. 工具：“助手”包含几个基本的tools，包括arxiv、python和艺术字
4. 其他：`chat/chat_qwenapi.py`对llm调用函数的过程进行了详细拆解（基于对modelscope-agent role play的理解）

## 基本结构说明

```
teach-chat/
├── LOCALPATH.py: 一些本地路径
├── README.md
├── avatar: 头像
├── chat: 定义chat函数
│   ├── chat_qwenapi.py：使用qwen api
│   └── chat_modelscope_agent.py：使用modelscope-agent
├── data: 存储原始教材和知识库
│   ├── chemistry: 化学教材
│   ├── physics: 物理教材
│   ├── knowledge_vector_chemistry: 化学知识库
│   │   ├── chemistry.faiss
│   │   └── chemistry.pkl
│   ├── knowledge_vector_physics: 物理知识库
│   │   ├── physics.faiss
│   │   └── physics.pkl
│   └── vector_store.ipynb: 知识库生成
├── history: 对话历史，每次对话“实时”加载、更新和保存
│   ├── chemistry.json
│   ├── chinese.json
│   └── helper.json
├── modelscope_agent: copy from modelsope-agent repo+修改+debug
├── ocr
│   ├── ocr_api.py
│   └── paddleocr.py
├── requirements.txt: ≈python3.10+modelsope-agent环境+ocr环境
├── run.sh: ```shell bash run.sh 运行：清空history和启动setup.py
└── setup.py
```

## 使用视频

https://www.bilibili.com/video/BV1eK42187sS/?vd_source=a10c8ca489cddbffa661b7501e54cf0c

## 生成展示

https://github.com/time1527/teach-chat/assets/154412155/f772f281-d9f0-4e84-8e0e-257c110dcdd6

https://github.com/time1527/teach-chat/assets/154412155/d6144c8d-2e35-4ef0-9346-ed9666823f74

https://github.com/time1527/teach-chat/assets/154412155/6ffbbf45-370d-409f-a261-fd9a78206257

## 环境搭建

1. 创建虚拟环境：
   ```shell
   conda create -n teachchat python=3.10
   conda activate teachchat
   ```
2. 安装各种：如使用非在线OCR（即，`from ocr.paddleocr import ocr`），还需安装 `paddleocr`和 `paddlepaddle-gpu`（`paddlepaddle`报错）
   ```shell
   pip install -r requirements.txt
   ```
3. 修改 `LOCALPATH.py`
4. `bash run.sh`

## 使用资源

avatar生成：https://www.modelscope.cn/studios/WordArt/WordArt/summary

教材下载：

物理必修第一册：https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/708256b6-6f06-4d14-89c7-4df16dfe3b81.pkg/pdf.pdf

物理必修第二册：https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/55baa3cc-156f-4358-8e28-bfa21a864450.pkg/pdf.pdf

物理必修第三册：https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/dcd8cc6b-5380-4008-a2d0-a061f24d34dd.pkg/pdf.pdf

化学必修第一册：https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/5cd19072-e40d-4a73-8580-7b7ada5d4005.pkg/pdf.pdf

化学必修第二册：https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/07f7d663-a867-4eb6-ad39-03b55dbd4a65.pkg/pdf.pdf

化学选择性必修1 化学反应原理：https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/3502fe81-b23e-4f68-aa3d-7921e7932ec9.pkg/pdf.pdf

化学选择性必修2 物质结构与性质：https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/b82cefe7-d631-4bde-baf9-352ca033cba4.pkg/pdf.pdf

化学选择性必修3 有机化学基础：https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets/c561d8ee-7c06-4cb1-9a4d-e34036f02d53.pkg/pdf.pdf

modelscope-agent：https://github.com/modelscope/modelscope-agent/tree/release/0.3.0

## 其他

前端：[LimingFang](https://github.com/LimingFang)
