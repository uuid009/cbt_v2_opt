import os
from typing import List
from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma   # ✅ 新版

# ======================
# 配置
# ======================
@dataclass
class DBConfig:
    knowledge_dir: str = "./data"
    persist_dir: str = "./chroma_db"
    collection_name: str = "rag_v2"

    chunk_size: int = 50
    chunk_overlap: int = 20

    embedding_model: str = "text-embedding-v4"
    api_key: str = os.getenv("DASHSCOPE_API_KEY", "")


# ======================
# 更新类
# ======================
class VectorDBUpdater:
    def __init__(self, config: DBConfig):
        self.config = config

        if not config.api_key:
            raise ValueError("请设置 DASHSCOPE_API_KEY")

        self.embedding = DashScopeEmbeddings(
            model=config.embedding_model,
            dashscope_api_key=config.api_key,
        )

        # ✅ 加载已有数据库（关键！）
        self.vector_store = Chroma(
            collection_name=config.collection_name,
            embedding_function=self.embedding,
            persist_directory=config.persist_dir,
        )

    # ======================
    # 加载 + 切分
    # ======================
    def load_documents(self) -> List[Document]:
        docs = []

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=["\n\n", "\n", "。", ".", "！", "？"],
        )

        for fname in os.listdir(self.config.knowledge_dir):
            if not fname.endswith(".txt"):
                continue

            path = os.path.join(self.config.knowledge_dir, fname)

            with open(path, "r", encoding="utf-8") as f:
                text = f.read()

            chunks = splitter.split_text(text)

            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) < 20:
                    continue

                docs.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "source": fname,
                            "chunk_id": i,
                        },
                    )
                )

        return docs

    # ======================
    # 去重（避免重复写入）
    # ======================
    def _dedup_new_docs(self, docs: List[Document]) -> List[Document]:
        existing = self.vector_store.get(include=["metadatas"])

        seen = set()
        for m in existing["metadatas"]:
            key = f"{m.get('source')}_{m.get('chunk_id')}"
            seen.add(key)

        new_docs = []
        for d in docs:
            key = f"{d.metadata['source']}_{d.metadata['chunk_id']}"
            if key not in seen:
                new_docs.append(d)

        return new_docs

    # ======================
    # 更新数据库
    # ======================
    def update(self):
        print("📥 加载文档...")
        docs = self.load_documents()
        print(f"总 chunk 数: {len(docs)}")

        print("🔍 去重...")
        new_docs = self._dedup_new_docs(docs)
        print(f"新增 chunk 数: {len(new_docs)}")

        if not new_docs:
            print("✅ 无需更新")
            return

        print("📦 写入向量库...")
        self.vector_store.add_documents(new_docs)

        print("✅ 更新完成！")


# ======================
# CLI
# ======================
if __name__ == "__main__":
    config = DBConfig()
    updater = VectorDBUpdater(config)
    updater.update()