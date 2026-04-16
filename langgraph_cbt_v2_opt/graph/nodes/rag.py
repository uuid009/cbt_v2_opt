"""
RAG检索节点 - 从知识库中检索相关内容
"""
from typing import Dict, Any, List
from rag.retriever import get_rag


def rag_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    RAG检索节点

    Args:
        state: 当前状态

    Returns:
        更新后的状态
    """
    
    if not state.get("need_rag", False):
        return {"knowledge": []}
    
    
    user_input = state.get("user_input", "")

    if not user_input:
        return state

    # 获取或创建检索器
    retriever = state.get("retriever")
    if retriever is None:
        retriever = get_rag()

    # 检索知识
    knowledge = retriever.retrieve(user_input)

    return {"knowledge": knowledge}


# 便捷函数
def retrieve_knowledge(query: str, retriever) -> List[str]:
    """便捷函数：检索知识"""
    if retriever is None:
        retriever = get_rag()
    return retriever.retrieve(query)