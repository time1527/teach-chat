import sys
import os
# current_file_dir = os.path.dirname(os.path.abspath("__file__"))
sys.path.append("/home/dola/teach-chat/data")
sys.path.append("/home/dola/teach-chat")
# print(current_file_dir)

from modelscope_agent.storage import KnowledgeVector
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
embedding = HuggingFaceEmbeddings(model_name="/home/dola/embedding/BAAI/bge-base-zh")

def create_db(subject):
    knowledge_vector = KnowledgeVector(
        storage_path="_".join(["knowledge_vector",subject]),
        embedding=embedding,
        index_name="_".join([subject,"index"]),
        use_cache=False
    )

    files_dir = "/home/dola/teach-chat/data/" + subject
    knowledge_vector.add(files_dir)

    knowledge_vector.save()
    storage_path = knowledge_vector.storage_path
    print(f"学科{subject}的教材已存入{storage_path}!")

def searchin(subject,question,top_k=3):
    knowledge_vector = KnowledgeVector(
        storage_path="_".join(["knowledge_vector",subject]),
        embedding=embedding,
        index_name="_".join([subject,"index"]),
    )

    search_results = knowledge_vector.search(question, top_k=top_k)
    
    return search_results

if __name__ == "__main__":
    create_db("physics")
    res = searchin("physics","牛顿第一定律是什么")
    print(res)