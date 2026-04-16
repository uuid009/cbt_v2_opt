"""
输入理解节点 - 分析用户输入的情绪、强度和风险
"""
from typing import Dict, Any
from utils.llm_client import LLMClient, get_default_client

# 情绪分类标签
EMOTION_LABELS = [
    "焦虑", "抑郁", "愤怒", "恐惧", "悲伤", "羞耻", "内疚",
    "孤独", "绝望", "无助", "平静", "希望", "感激", "其他"
]

# 强度等级
INTENSITY_LEVELS = ["低", "中", "高"]

# 风险等级
RISK_LEVELS = ["low", "medium", "high"]


def perception_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    输入理解节点 - 分析用户输入

    Args:
        state: 当前状态

    Returns:
        更新后的状态
    """
    user_input = state.get("user_input", "")

    if not user_input:
        return state

    # 获取LLM客户端
    # llm = state.get("llm_client")
    # if llm is None:
    #     llm = get_default_client()
    
    
    llm = LLMClient(model_name="qwen-flash")

    # 构建分析prompt
    prompt = _build_analysis_prompt(user_input)

    # 调用LLM
    messages = [{"role": "user", "content": prompt}]
    result = llm.chat(messages, temperature=0.3, max_tokens=500)

    # 解析结果
    parsed = _parse_analysis_result(result)

    # 更新状态
    return {
        "emotion": parsed.get("emotion", "其他"),
        "intensity": parsed.get("intensity", "中"),
        "risk_level": parsed.get("risk_level", "low"),
        "analysis": parsed.get("analysis", ""),
    }


def _build_analysis_prompt(user_input: str) -> str:
    """构建分析prompt"""
    return f"""请分析以下用户输入的情绪状态。

用户输入：{user_input}

请从以下维度进行分析：
1. 情绪分类：从[{", ".join(EMOTION_LABELS)}]中选择最匹配的一个
2. 情绪强度：从[{", ".join(INTENSITY_LEVELS)}]中选择
3. 风险等级：从[{", ".join(RISK_LEVELS)}]中选择
   - low: 正常情绪波动，可以正常对话
   - medium: 情绪较强烈，可能需要更多支持
   - high: 有自伤/自杀风险，需要紧急干预

请以JSON格式返回：
{{"emotion": "情绪", "intensity": "强度", "risk_level": "风险等级", "analysis": "简短分析说明"}}"""


def _parse_analysis_result(result: str) -> Dict[str, Any]:
    """解析LLM返回的分析结果"""
    import json
    import re

    # 尝试提取JSON
    try:
        return json.loads(result)
    except:
        pass

    # 尝试从文本中提取
    json_match = re.search(r'\{[^}]+\}', result, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            return {
                "emotion": parsed.get("emotion", "其他"),
                "intensity": parsed.get("intensity", "中"),
                "risk_level": parsed.get("risk_level", "low"),
                "analysis": parsed.get("analysis", ""),
            }
        except:
            pass

    # 降级方案：基于关键词简单判断
    print("[DEBUG 感知分析] 降级分析")
    return _fallback_analysis(result)


def _fallback_analysis(result: str) -> Dict[str, Any]:
    """降级分析 - 当无法解析JSON时使用"""
    result_lower = result.lower()

    # 风险检测
    risk = "low"
    risk_keywords = {
        "high": ["自杀", "自伤", "不想活", "死了", "结束生命", "割腕", "跳楼"],
        "medium": ["绝望", "无助", "崩溃", "坚持不住", "太痛苦"],
    }
    for level, keywords in risk_keywords.items():
        if any(k in result_lower for k in keywords):
            risk = level
            break

    # 情绪检测
    emotion = "其他"
    emotion_keywords = {
        "焦虑": ["焦虑", "担心", "紧张", "害怕"],
        "抑郁": ["抑郁", "难过", "伤心", "失望", "绝望"],
        "愤怒": ["愤怒", "生气", "气愤", "恼火"],
        "恐惧": ["恐惧", "害怕", "惊恐"],
        "悲伤": ["悲伤", "难过", "伤心", "哭"],
        "孤独": ["孤独", "寂寞", "没人"],
    }
    for emo, keywords in emotion_keywords.items():
        if any(k in result_lower for k in keywords):
            emotion = emo
            break

    return {
        "emotion": emotion,
        "intensity": "中",
        "risk_level": risk,
        "analysis": "基于关键词分析",
    }


# 便捷函数
def analyze_input(user_input: str, llm_client: LLMClient = None) -> Dict[str, Any]:
    """便捷函数：分析用户输入"""
    # 模拟状态调用
    state = {"user_input": user_input, "llm_client": llm_client}
    return perception_node(state)