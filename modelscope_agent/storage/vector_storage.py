import os
from typing import Dict, List, Union

import json
from langchain.schema import Document
from langchain_community.embeddings import ModelScopeEmbeddings
from langchain_community.vectorstores import FAISS, VectorStore
from langchain_core.embeddings import Embeddings
from modelscope_agent.utils.parse_doc import parse_doc
from .base import BaseStorage

from LOCALPATH import EMBEDDING_PATH,RERANK_PATH
from langchain_community.embeddings import HuggingFaceEmbeddings
SUPPORTED_KNOWLEDGE_TYPE = ['txt', 'md', 'pdf', 'docx', 'pptx', 'md']

# used for rerank
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained(RERANK_PATH)
rerank_model = AutoModelForSequenceClassification.from_pretrained(RERANK_PATH).cuda()

# used for reorder
from langchain_community.document_transformers import LongContextReorder

# used for selfquery
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo
metadata_field_info = [
    AttributeInfo(
        name="source",
        description="来源",
        type="string",
    ),
    AttributeInfo(
        name="path",
        description="路径",
        type="string",
    ),
    AttributeInfo(
        name="page",
        description="页码",
        type="int",
    ),
]
document_content_description = "教材"

class VectorStorage(BaseStorage):

    def __init__(self,
                 storage_path: str,
                 index_name: str,
                 embedding: Embeddings = None,
                 vs_cls: VectorStore = FAISS,
                 vs_params: Dict = {},
                 index_ext: str = '.faiss',
                 use_cache: bool = True,
                 **kwargs):
        self.storage_path = storage_path # 存储/加载路径
        self.index_name = index_name
        self.embedding = embedding or HuggingFaceEmbeddings(
            model_name = EMBEDDING_PATH) or ModelScopeEmbeddings(
            model_id='damo/nlp_gte_sentence-embedding_chinese-base')
        self.vs_cls = vs_cls
        self.vs_params = vs_params
        self.index_ext = index_ext
        if use_cache:
            self.vs = self.load()
        else:
            self.vs = None


    def construct(self, docs):
        assert len(docs) > 0
        if isinstance(docs[0], str):
            self.vs = self.vs_cls.from_texts(docs, self.embedding,
                                             **self.vs_params)
        elif isinstance(docs[0], Document):
            self.vs = self.vs_cls.from_documents(docs, self.embedding,
                                                 **self.vs_params)


    def search(self, query: str, top_k=3) -> List[str]:
        if self.vs is None:
            return []
        res = self.vs.similarity_search(query, k=top_k*2) # [Document]
        res = [r.page_content for r in res] # [string]
        # if 'page' in res[0].metadata:
        #     res.sort(key=lambda doc: doc.metadata['page'])
        # return [r.page_content for r in res]
        
        # TODO: 自查询和rerank 2024/2/21
        """
        # self query:"物理必修一里面讲了牛顿什么"
        retriever = SelfQueryRetriever.from_llm(
            llm,
            self.vs,
            document_content_description,
            metadata_field_info,
            search_kwargs={"k": top_k}
        )
        res = retriever.get_relevant_documents(query)
        """
        # modified: 重排序 2024/2/22
        pairs = [[query,r] for r in res]
        inputs = tokenizer(pairs, padding=True, truncation=True, return_tensors='pt', max_length=1024)
        with torch.no_grad():
            inputs = {key: inputs[key].cuda() for key in inputs.keys()}
            scores = rerank_model(**inputs, return_dict=True).logits.view(-1, ).float().cpu().numpy().tolist()
            scores_sorted,res_sorted = zip(*sorted(zip(scores, res)))
            # for i in range(top_k*2):
            #     print(f"score = {scores_sorted[i]},content = {res_sorted[i]}")

        # 按照rerank score从大到小的top_k个
        res = [r for r in res_sorted[::-1][:top_k]]

        # modified: Lost in the middle reorder 2024/2/22
        reordering = LongContextReorder()
        res_reordered = reordering.transform_documents(res)
        return res_reordered
        

    def add(self, docs: Union[List[str], List[Document]]):
        assert len(docs) > 0
        if isinstance(docs[0], str):
            self.vs.add_texts(docs, **self.vs_params)
        elif isinstance(docs[0], Document):
            self.vs.add_documents(docs, **self.vs_params)


    def _get_index_and_store_name(self, index_ext='.index', pkl_ext='.pkl'):
        index_file = os.path.join(self.storage_path,
                                  f'{self.index_name}{index_ext}')
        store_file = os.path.join(self.storage_path,
                                  f'{self.index_name}{pkl_ext}')
        return index_file, store_file


    def load(self) -> Union[VectorStore, None]:
        if not self.storage_path or not os.path.exists(self.storage_path):
            return None
        index_file, store_file = self._get_index_and_store_name(
            index_ext=self.index_ext)

        if not (os.path.exists(index_file) and os.path.exists(store_file)):
            return None

        return self.vs_cls.load_local(self.storage_path, self.embedding,
                                      self.index_name)


    def save(self):
        if self.vs:
            self.vs.save_local(self.storage_path, self.index_name)


class KnowledgeVector(VectorStorage):

    @staticmethod
    def file_preprocess(file_path: Union[str, List[str]]) -> List[Dict]:
        all_files = []
        if isinstance(file_path, str) and os.path.isfile(file_path):
            all_files.append(file_path)
        elif isinstance(file_path, list):
            for f in file_path:
                if os.path.isfile(f):
                    all_files.append(f)
        elif os.path.isdir(file_path):
            for root, dirs, files in os.walk(file_path):
                for f in files:
                    all_files.append(os.path.join(root, f))
        else:
            raise ValueError('file_path must be a file or a directory')

        docs = []
        for f in all_files:
            if f.split('.')[-1].lower() in SUPPORTED_KNOWLEDGE_TYPE:
                doc_list = parse_doc(f) # spliter: chunk size/chunk overlap
                if len(doc_list) > 0:
                    docs.extend(doc_list)
        return docs # 有metadata

    # should load and save
    def add(self, file_path: Union[str, list]):
        custom_docs = KnowledgeVector.file_preprocess(file_path)
        if len(custom_docs) > 0:
            # modify: 2024/2/19
            # text_docs = [docs['page_content'] for docs in custom_docs]
            text_docs = custom_docs

            if self.vs is None:
                self.construct(text_docs)
            else:
                super().add(text_docs)
