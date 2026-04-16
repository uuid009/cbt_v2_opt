"""
LangGraph 图定义
定义心理Agent的工作流程图
"""
from langgraph.graph import StateGraph, END
from typing import Dict, Any

from graph.state import AgentState
from graph.nodes import (
    perception_node,
    rag_node,
    memory_node,
    update_memory_node,
    get_memory_summary_node,
    policy_node,
    generator_node,
    safety_node,
    high_risk_node,
    router_node,
    reviewer_node
)


def create_graph() -> StateGraph:
    """
    创建LangGraph工作流图

    Returns:
        编译后的StateGraph
    """
    # 创建图
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("memory", memory_node)           # 获取记忆
    workflow.add_node("perception", perception_node)    # 输入理解
    workflow.add_node("router", router_node)           # 路由决策
    workflow.add_node("rag", rag_node)                 # 知识检索
    workflow.add_node("policy", policy_node)           # 策略决策
    workflow.add_node("generator", generator_node)     # 回复生成
    workflow.add_node("reviewer", reviewer_node) # 内容审核
    workflow.add_node("safety", safety_node)           # 安全检查
    workflow.add_node("update_memory", update_memory_node)  # 更新记忆
    

    # 设置入口点
    workflow.set_entry_point("memory")

    # 添加边 - 主流程
    workflow.add_edge("memory", "perception")
    # workflow.add_edge("perception", "rag")
    workflow.add_edge("perception", "router")
    workflow.add_edge("rag", "policy")
    workflow.add_edge("policy", "generator")
    workflow.add_edge("generator", "reviewer")
    workflow.add_edge("reviewer", "safety")

    # 条件边 - 安全检查后根据风险等级分支
    workflow.add_conditional_edges(
        "safety",
        _route_by_risk,
        {
            "high_risk": "high_risk",
            "safe": "update_memory",
        }
    )
    
    # 判断是否需要走rag
    workflow.add_conditional_edges(
        "router",
        lambda state: "rag" if state.get("need_rag") else "skip_rag",
        {
            "rag": "rag",
            "skip_rag": "policy",
        }
    )
    
    # 审查结果: 重做或继续
    workflow.add_conditional_edges(
        "reviewer",
        _should_regenerate,
        {
            "regenerate": "generator",
            "end": "safety",
        }
    )

    # 高风险处理
    workflow.add_node("high_risk", high_risk_node)
    workflow.add_edge("high_risk", "update_memory")

    # 更新记忆后结束
    workflow.add_edge("update_memory", END)

    # 编译图
    return workflow.compile()


def _should_regenerate(state: Dict[str, Any]) -> str:
    """判断是否需要重新生成"""
    approved = state.get("approved", True)
    retry_count = state.get("retry_count", 0)

    if approved:
        return "end"

    if retry_count >= 2:
        print("[MultiAgent] max retry reached")
        return "end"

    print(f"[MultiAgent] regenerate, retry {retry_count}")
    return "regenerate"


def _route_by_risk(state: Dict[str, Any]) -> str:
    """
    根据风险等级路由

    Args:
        state: 当前状态

    Returns:
        路由目标
    """
    risk_level = state.get("risk_level", "low")

    if risk_level == "high":
        print("langgraph: high risk")
        return "high_risk"

    return "safe"


# 全局图实例
_graph = None


def get_graph() -> StateGraph:
    """获取图实例（单例）"""
    global _graph
    if _graph is None:
        _graph = create_graph()
    return _graph


def run_agent(
    user_input: str,
    llm_client=None,
    memory_storage: str = "./memory_data.json",
    knowledge_dir: str = "/home/lenovo/zch/Agent/data",
) -> str:
    """
    运行Agent

    Args:
        user_input: 用户输入
        llm_client: LLM客户端
        memory_storage: 记忆存储路径
        knowledge_dir: 知识库目录

    Returns:
        Agent回复
    """
    from memory.memory import Memory
    from rag.retriever import get_rag

    # 初始化组件
    memory = Memory()
    retriever = get_rag()

    print(f"[DEBUG run_agent] user_input: {user_input}")
    # print(f"[DEBUG run_agent] short_term before add_user_input: {memory.data.get('short_term', [])}")

    # 预先将用户输入加入记忆
    memory.add_user_input(user_input)

    # print(f"[DEBUG run_agent] short_term after add_user_input: {memory.data.get('short_term', [])}")

    # 初始状态
    initial_state = {
        "user_input": user_input,
        "emotion": "",
        "intensity": "",
        "risk_level": "",
        "analysis": "",
        "knowledge": [],
        "short_term": [],
        "long_term": [],
        "profile": {},
        "strategy": "",
        "strategy_instruction": "",
        "response": "",
        "is_safe": True,
        "final_response": "",
        "conversation_turn": 0,
        "error": None,
        # 组件实例
        "llm_client": llm_client,
        "memory": memory,
        "memory_storage": memory_storage,
        "retriever": retriever,
        "knowledge_dir": knowledge_dir,
    }
    
    
    print(f'\n Agent Runing... \n')
    # 运行图
    graph = get_graph()
    result = graph.invoke(initial_state)

    print(f"[DEBUG run_agent] final_response: {result.get('final_response', '')[:100]}...")

    return result.get("final_response", "")


if __name__ == "__main__":
    # 测试
    # from utils.llm_client import LLMClient

    # llm = LLMClient()

    # print("=== LangGraph 心理CBT Agent 测试 ===")
    # print("输入 'quit' 退出\n")

    # while True:
    #     user_input = input("你: ")
    #     if user_input.lower() in ["quit", "exit", "退出"]:
    #         break

    #     response = run_agent(user_input, llm)
    #     print(f"助手: {response}\n")
    
    graph = get_graph()
    graph_png = graph.get_graph().draw_mermaid_png()
    with open("/home/lenovo/zch/Agent/langgraph_cbt_v2_opt/graph_cbt.png", "wb") as f:
        f.write(graph_png)