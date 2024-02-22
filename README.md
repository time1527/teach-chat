# teach-chat

## 基本结构说明
```
teach-chat/
├── LOCALPATH.py: 一些本地路径
├── README.md
├── avatar: 头像
├── chat: 定义chat函数
│   ├── chat_api.py
│   └── chat_modelscope_agent.py
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
├── history: 对话历史
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
## 效果视频

【待上传】

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
