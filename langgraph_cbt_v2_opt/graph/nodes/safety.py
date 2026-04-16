from typing import Dict, Any
from safety.safety import SafetyService, RiskLevel


# 全局单例（避免重复初始化）
safety_service = SafetyService()


def safety_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    安全检查节点（主入口）

    流程：
    1. 输入安全检测
    2. 是否拦截
    3. 输出安全处理
    """

    user_input = state.get("user_input", "")
    response = state.get("response", "")

    # 空响应兜底
    if not response:
        return {
            "is_safe": False,
            "final_response": "谢谢你的分享，我在这里倾听。",
            "risk_level": RiskLevel.LOW
        }

    # ===== 调用 SafetyService =====
    final_response = safety_service.run(
        user_input=user_input,
        response=response,
        context=state
    )

    # ===== 判断风险等级 =====
    input_check = safety_service.engine.check_input(user_input, state)
    risk_level = input_check["risk_level"]

    is_safe = (
        risk_level < RiskLevel.HIGH
        and final_response == response
    )
    
    
    # 展示is_safe, final_response, risk_level, response
    retry_count = state.get("retry_count", 0)
    print("retry_count:", retry_count)

    print("is_safe:", is_safe)
    print("final_response:", final_response)
    print("risk_level:", risk_level)
    print("response:", response)

    return {
        "is_safe": is_safe,
        "final_response": final_response,
        "risk_level": risk_level,
    }


# ========================
# 高风险节点（企业级安全版）
# ========================
    
    
def high_risk_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    高风险处理节点 - 当检测到高风险时的特殊处理

    Args:
        state: 当前状态

    Returns:
        更新后的状态
    """
    # 高风险情况，生成特殊响应
    llm = state.get("llm_client")
    if llm is None:
        from utils.llm_client import get_default_client
        llm = get_default_client()

    user_input = state.get("user_input", "")

    prompt = f"""用户输入了可能存在自伤风险的内容：

    用户：{user_input}

    请提供一个简短、温暖且支持性的回应，要求：
    - 表达关心与理解
    - 不否定或忽视用户感受
    - 语气自然、不过度说教
    - 温和地建议寻求专业帮助

    ⚠️ 回复中必须逐字包含以下内容（不得改写或省略）：

    如果你有伤害自己的想法，请尽快联系专业帮助：
    - 中国心理危机干预热线：400-161-9995
    - 北京心理危机中心：010-82951332

    在此基础上，可以自然地补充一句支持性的话，例如表达“我在这里陪你”或询问“你现在是否安全”。
    """

    response = llm.chat(
        [{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=300,
    )

    return {
        "is_safe": False,
        "final_response": response,
    }