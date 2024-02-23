from typing import Dict, Iterator, List, Optional, Union

import json
from modelscope_agent.agent import Agent
from modelscope_agent.llm.base import BaseChatModel
from modelscope_agent.storage import KnowledgeVector
from modelscope_agent.utils.logger import agent_logger as logger

from .base import Memory


class MemoryWithRetrievalKnowledge(Memory, Agent):

    def __init__(self,
                 function_list: Optional[List[Union[str, Dict]]] = None,
                 llm: Optional[Union[Dict, BaseChatModel]] = None,
                 storage_path: Optional[str] = None,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 use_knowledge_cache: bool = True,
                 **kwargs):
        # name同时作为agent的name（没啥用）和KnowledgeVector的index_name（很有用）
        Memory.__init__(self, path=kwargs.get('memory_path', ''))
        Agent.__init__(
            self,
            function_list=function_list,
            llm=llm,
            name=name,
            description=description)

        # allow vector storage to save knowledge
        self.store_knowledge = KnowledgeVector(
            storage_path, name, use_cache=use_knowledge_cache)


    def _run(self,
             query: str = None,
             url: str = None,
             max_token: int = 4000,
             top_k: int = 3,
             **kwargs) -> Union[str, Iterator[str]]:
        # no need for llm in this agent yet, all the operation could be handled by simple logic
        if url:
            try:
                url = json.loads(url)
            except json.JSONDecodeError:
                pass

            # add file to index
            try:
                self.store_knowledge.add(url)
                self.store_knowledge.save()
            except Exception as e:
                logger.query_warning(
                    uuid=kwargs.get('uuid_str', 'local_user'),
                    details=str(e),
                    message=f'fail to learn knowledge from {url}')

            # save store knowledge

        # no query then return None
        if not query:
            return None

        # search records
        # modified: 2024/2/19
        # TODO：压缩
        records = self.store_knowledge.search(query, top_k=top_k)

        # limit length
        concatenated_records = '\n'.join(records)
        if len(concatenated_records) > max_token:
            single_max_token = int(max_token / len(records))
            concatenated_records = '\n'.join(
                [record[0:single_max_token - 1] for record in records])

        return concatenated_records