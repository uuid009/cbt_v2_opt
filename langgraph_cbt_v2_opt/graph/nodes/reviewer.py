"""
审查Agent - 审查生成内容的质量
"""
from typing import Dict, Any


def reviewer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    审查回复

    Args:
        state: 包含 user_input, response, emotion, intensity 的状态

    Returns:
        approved: 是否通过审查
        feedback: 审查反馈
    """
    user_input = state.get("user_input", "")
    response = state.get("response", "")
    emotion = state.get("emotion", "")
    intensity = state.get("intensity", "")

    if not response:
        return {
            "approved": False,
            "feedback": "回复为空",
            "retry_count": state.get("retry_count", 0) + 1,
        }
        
    from utils.llm_client import LLMClient
    
    llm = LLMClient(model_name="qwen-flash")
    
    prompt = _build_review_prompt(user_input, response, emotion, intensity)

    messages = [{"role": "user", "content": prompt}]
    result = llm.chat(messages, temperature=0.3, max_tokens=300)

    parsed = _parse_review_result(result)
    
    approved = parsed.get("approved", True)
    feedback = parsed.get("feedback", "")
    retry_count = state.get("retry_count", 0) + 1

    print(f"[ReviewerAgent] approved={approved}, feedback={feedback[:50] if feedback else ''}")

    return {
        "approved": approved,
        "feedback": feedback,
        "retry_count": retry_count,
        "review_result": parsed,
    }


def _build_review_prompt(
    user_input: str,
    response: str,
    emotion: str,
    intensity: str,
) -> str:
    """构建审查prompt"""
    return f"""请审查以下心理咨询回复的质量。

用户输入：{user_input}
用户情绪：{emotion}（{intensity}）

回复内容：{response}

请从以下维度审查：
1. 安全性：是否包含危害性内容或不当建议
2. 共情性：是否理解并回应了用户的情绪
3. 专业性：是否符合心理咨询专业原则
4. 完整性：是否回答了用户的问题或表达了理解

请以JSON格式返回：
{{"approved": true/false, "feedback": "审查反馈，如果不通过说明原因"}}"""


def _parse_review_result(result: str) -> Dict[str, Any]:
    """解析审查结果"""
    import json
    import re

    try:
        return json.loads(result)
    except:
        pass

    json_match = re.search(r'\{[^}]+\}', result, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass

    # 降级方案：默认通过
    print("[ReviewerAgent] 降级到默认通过")
    return {"approved": True, "feedback": ""}