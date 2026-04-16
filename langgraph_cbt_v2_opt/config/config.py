# config.py
import os
from dataclasses import dataclass

@dataclass
class Config:
    # 路径相关
    persist_dir: str = "./chroma_db"
    collection_name: str = "rag_v2"
    knowledge_dir: str = "./data"

    # 检索参数
    top_k: int = 8
    rerank_top_k: int = 3

    # 模型
    embedding_model: str = "text-embedding-v4"
    rerank_model: str = "qwen3-rerank"

    # API
    api_key: str = os.getenv("DASHSCOPE_API_KEY", "")

    # chunk
    chunk_size: int = 50
    chunk_overlap: int = 20
    
    # 生成参数
    temperature=0.7
    max_tokens=500
    
    # 缓存
    storage_path: str = "./memory_data.json"
    short_term_max: int = 100


# 创建一个全局配置实例（可选）
config = Config()