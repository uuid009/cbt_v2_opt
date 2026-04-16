"""
回复生成节点 - 融合所有信息生成回复
"""
from typing import Dict, Any, List
from generator.prompt_builder import PromptBuilder
from utils.llm_client import LLMClient, get_default_client


def generator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    回复生成节点

    Args:
        state: 当前状态

    Returns:
        更新后的状态（包含生成的回复）
    """
    # 获取必要信息
    user_input = state.get("user_input", "")
    short_term = state.get("short_term", [])
    long_term = state.get("long_term", [])
    profile = state.get("profile", {})
    knowledge = state.get("knowledge", [])
    strategy_instruction = state.get("strategy_instruction", "")

    # 构建上下文
    context = _build_context(short_term)

    # 构建prompt
    prompt_builder = PromptBuilder()
    messages = prompt_builder.build(
        user_input=user_input,
        state={
            "emotion": state.get("emotion", ""),
            "intensity": state.get("intensity", ""),
            "risk_level": state.get("risk_level", ""),
            "analysis": state.get("analysis", ""),
        },
        context=context,
        long_term=long_term,
        profile=profile,
        knowledge=knowledge,
        strategy_instruction=strategy_instruction,
    )

    # 获取LLM客户端
    llm = state.get("llm_client")
    if llm is None:
        llm = get_default_client()

    # 调用LLM
    response = llm.chat(
        messages=messages,
        temperature=0.7,
        max_tokens=500,
    )

    # 后处理
    response = _post_process(response)

    return {"response": response}


def _build_context(short_term: List[Dict[str, str]]) -> str:
    """构建对话上下文"""
    if not short_term:
        return "（暂无对话历史）"

    context_parts = []
    for msg in short_term[-10:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            context_parts.append(f"用户: {content}")
        else:
            context_parts.append(f"助手: {content}")

    return "\n".join(context_parts)


def _post_process(response: str) -> str:
    """后处理回复"""
    response = response.strip()

    if not response:
        return "谢谢你的分享，我在这里倾听。"

    return response


# 便捷函数
def generate_response(
    user_input: str,
    state: Dict[str, Any],
    context: str,
    long_term: List[str],
    profile: Dict[str, Any],
    knowledge: List[str],
    strategy_instruction: str,
    llm_client: LLMClient = None,
) -> str:
    """便捷函数：生成回复"""
    # 模拟状态调用
    full_state = {
        "user_input": user_input,
        "short_term": [],
        "long_term": long_term,
        "profile": profile,
        "knowledge": knowledge,
        "strategy_instruction": strategy_instruction,
        "emotion": state.get("emotion", ""),
        "intensity": state.get("intensity", ""),
        "risk_level": state.get("risk_level", ""),
        "analysis": state.get("analysis", ""),
        "llm_client": llm_client,
    }
    result = generator_node(full_state)
    return result.get("response", "")