# ===== 必须在所有 import 之前设置镜像源 =====
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["TRANSFORMERS_OFFLINE"] = "0"

# ===== 加载 .env 环境变量 =====
from dotenv import load_dotenv
load_dotenv()

from typing import List

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore

# ===== 常量配置 =====
QDRANT_LOCAL_PATH = "./qdrant_resume_db"  # 本地 Qdrant 存储路径
COLLECTION_NAME = "resume_collection"      # 集合名称
EMBEDDING_MODEL = "BAAI/bge-base-zh-v1.5" # BGE 中文向量模型（768维）

def DeepSeek():
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=os.environ.get("deepseek"),
        base_url="https://api.deepseek.com"
    )

def DeepSeekR1():
    return ChatOpenAI(
        model="deepseek-reasoner",
        api_key=os.environ.get("deepseek"),
        base_url="https://api.deepseek.com"
    )

def DeepSeekV4Flash():
    return ChatOpenAI(
        model="deepseek-v4-flash",
        api_key=os.environ.get("deepseek"),
        base_url="https://api.deepseek.com",
        streaming=False,
        request_timeout=120,
    )

def DeepSeekV4Pro():
    return ChatOpenAI(
        model="deepseek-v4-pro",
        api_key=os.environ.get("deepseek"),
        base_url="https://api.deepseek.com"
    )

def TongyiEmbedding() -> HuggingFaceEmbeddings:
    """初始化本地 BGE 中文向量模型"""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

def QdrantVecStoreFromDocs(docs:List[Document]):
    """从文档列表创建本地 Qdrant 向量库"""
    eb=TongyiEmbedding()
    return QdrantVectorStore.from_documents(docs,eb,path=QDRANT_LOCAL_PATH,collection_name=COLLECTION_NAME)

def QdrantVecStore(eb: HuggingFaceEmbeddings, collection_name: str):
    """连接已有的本地 Qdrant 集合"""
    return  QdrantVectorStore.\
        from_existing_collection(embedding=eb,
         path=QDRANT_LOCAL_PATH,
          collection_name=collection_name)