"""
LangGraph State 定义
定义心理Agent的状态结构
"""
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import MessagesState


class AgentState(TypedDict):
    """心理Agent的状态定义"""
    # 用户输入
    user_input: str

    # 情绪分析结果
    emotion: str
    intensity: str
    risk_level: str
    analysis: str

    # 是否需要进行RAG检索
    need_rag: bool
    
    # RAG检索结果
    knowledge: List[str]

    # 记忆系统
    short_term: List[Dict[str, str]]  # [{"role": "user/assistant", "content": "..."}]
    long_term: List[str]
    profile: Dict[str, Any]  # {"personality": [], "communication_style": [], "concerns": [], "risk_flag": ""}

    # 策略决策
    strategy: str
    strategy_instruction: str

    # 生成结果
    response: str

    # 安全检查结果
    is_safe: bool
    final_response: str
    approved: bool
    retry_count: int
    feedback: str

    # 元数据
    conversation_turn: int
    error: Optional[str]
    
    # 组件实例
    llm_client: Any 
    memory: Any
    memory_storage: str
    retriever: Any
    knowledge_dir: str