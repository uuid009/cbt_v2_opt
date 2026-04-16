"""
RAG v2（企业级最终版）
- MultiQuery
- MMR
- Qwen3 Rerank
- Agent Tool化
"""

import os
from typing import List
from dataclasses import dataclass
from functools import lru_cache

import dashscope
from langchain_core.documents import Document
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma
from utils.llm_client import LLMClient
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config.config import config

# ======================
# 配置
# ======================
@dataclass
class RAGConfig:
    persist_dir = config.persist_dir
    collection_name = config.collection_name
    knowledge_dir = config.knowledge_dir

    top_k = config.top_k
    rerank_top_k = config.rerank_top_k

    embedding_model = config.embedding_model
    rerank_model = config.rerank_model

    api_key = config.api_key

    chunk_size = config.chunk_size
    chunk_overlap = config.chunk_overlap


# ======================
# Multi Query
# ======================
class MultiQueryGenerator:
    def __init__(self, llm):
        self.llm = llm

        self.prompt = PromptTemplate(
            input_variables=["query"],
            template="""
你是一个检索优化助手，请对用户问题生成3个不同表达方式，用于向量检索。

原问题：
{query}

要求：
1. 语义相同
2. 表达不同
3. 更利于检索

输出格式：
1.xxx
2.xxx
3.xxx
""",
        )

    def generate(self, query: str) -> List[str]:
        try:
            # resp = self.llm.invoke(self.prompt.format(query=query))
            
            resp = self.llm.chat(
                messages=[
                    {"role": "user", "content": self.prompt.format(query=query)}
                ],
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
            
            
            if isinstance(resp, str):
                content = resp
            else:
                content = resp.content  # 或 resp.output... 看你封装

            
            print(f"[INFO] MultiQuery结果: {content}")
            import re
            queries = re.findall(r"\d+[\.、]\s*(.+)", content)

            print(f"[INFO] MultiQuery结果: {queries}")
            return queries[:3] if queries else [query]

        except Exception as e:
            print(f"[WARN] MultiQuery失败: {e}")
            return [query]


# ======================
# Qwen3 Reranker
# ======================
class QwenReranker:
    def __init__(self, api_key: str, model: str):
        self.model = model
        dashscope.api_key = api_key

    def rerank(self, query: str, docs: List[Document], top_k: int) -> List[Document]:
        if not docs:
            return []

        texts = [d.page_content for d in docs]

        try:
            resp = dashscope.TextReRank.call(
                model=self.model,
                query=query,
                documents=texts,
                top_n=top_k,
            )

            if resp.status_code != 200:
                raise Exception(resp)

            results = resp.output["results"]

            reranked = []
            for r in results:
                idx = r["index"]
                score = r["relevance_score"]

                doc = docs[idx]
                doc.metadata["rerank_score"] = score
                reranked.append(doc)

            return reranked

        except Exception as e:
            print(f"[ERROR] rerank失败: {e}")
            return docs[:top_k]


# ======================
# 主 RAG
# ======================
class AdvancedRAG:
    def __init__(self, config: RAGConfig):
        self.config = config

        if not config.api_key:
            raise ValueError("请设置 DASHSCOPE_API_KEY")

        # embedding
        self.embedding = DashScopeEmbeddings(
            model=config.embedding_model,
            dashscope_api_key=config.api_key,
        )

        # llm（用于MultiQuery）
        self.llm = LLMClient(
                    model_provider="dashscope",
                    model_name="qwen-flash",
                )

        # 向量库
        if not os.path.exists(config.persist_dir) or not os.listdir(config.persist_dir):
            print("⚡ 首次构建向量库")
            self.build_vector_store()
        else:
            self.vector_store = Chroma(
                collection_name=config.collection_name,
                embedding_function=self.embedding,
                persist_directory=config.persist_dir,
            )

        # 组件
        self.multi_query = MultiQueryGenerator(self.llm)
        self.reranker = QwenReranker(
            api_key=config.api_key,
            model=config.rerank_model,
        )

    # ======================
    # 核心流程
    # ======================
    def retrieve(self, query: str) -> List[str]:
        # 1️⃣ query扩展
        queries = self.multi_query.generate(query)
        queries.append(query)
        
        print(f"queries: {queries}")

        # 2️⃣ 多路召回
        all_docs = []
        for q in queries:
            docs = self.vector_store.max_marginal_relevance_search(
                q,
                k=self.config.top_k,
                fetch_k=self.config.top_k * 2,
            )
            all_docs.extend(docs)

        # 3️⃣ 去重
        unique_docs = self._dedup(all_docs)
        
        # 4️⃣ rerank
        reranked = self.reranker.rerank(
            query,
            unique_docs,
            self.config.rerank_top_k,
        )

        return [d.page_content for d in reranked]

    def _dedup(self, docs: List[Document]) -> List[Document]:
        seen = set()
        result = []

        for d in docs:
            key = d.page_content[:100]
            if key not in seen:
                seen.add(key)
                result.append(d)

        return result
    
    
    def load_documents(self):
        docs = []

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,        # 每块大小
            chunk_overlap=self.config.chunk_overlap,     # 重叠（非常关键）
            separators=["\n\n", "\n", "。", ".", "！", "？"],
        )

        for fname in os.listdir(self.config.knowledge_dir):
            if not fname.endswith(".txt"):
                continue

            path = os.path.join(self.config.knowledge_dir, fname)

            with open(path, "r", encoding="utf-8") as f:
                text = f.read()

            # ✨ 切分
            chunks = splitter.split_text(text)

            # ✨ 转 Document（带 metadata）
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

    def build_vector_store(self):
        docs = self.load_documents()

        self.vector_store = Chroma.from_documents(
            documents=docs,   # ⚠️ 注意这里变了
            embedding=self.embedding,
            collection_name=self.config.collection_name,
            persist_directory=self.config.persist_dir,
        )

# ======================
# Agent Tool
# ======================
class RAGTool:
    name = "knowledge_search"
    description = "用于检索知识库信息"

    def __init__(self):
        self.rag = get_rag()

    def run(self, query: str) -> str:
        results = self.rag.retrieve(query)
        return "\n\n".join(results)


# ======================
# 单例（性能关键）
# ======================
@lru_cache(maxsize=1)
def get_rag():
    config = RAGConfig()
    return AdvancedRAG(config)


# ======================
# 对外接口
# ======================
def retrieve_knowledge(query: str) -> List[str]:
    rag = get_rag()
    return rag.retrieve(query)


# ======================
# 测试
# ======================
if __name__ == "__main__":
    rag = get_rag()

    query = "cbt的原理"
    results = rag.retrieve(query)

    print("\n=== 最终结果 ===")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r[:120]}...\n")