"""
策略决策节点 - 增强版 Few-Shot 优化
"""
from typing import Dict, Any, Tuple

# 策略类型常量
class Strategy:
    EMPATHY = "empathy"
    EXPLORATION = "exploration"
    GENTLE_EXPLORATION = "gentle_exploration"
    CBT_REFRAME = "cbt_reframe"
    SUPPORT = "support"
    GUIDANCE = "guidance"

# --- Few-Shot 优化的策略指令模板 ---
STRATEGY_INSTRUCTIONS = {
    Strategy.EMPATHY: (
        "【策略：共情接纳】\n"
        "目标：让用户感到被看见、被听见、被理解。\n"
        "执行原则：使用情感反映技术，不做评价，不急于改变对方。\n"
        "示例：\n"
        "- 用户：‘我真的受够了这工作。’\n"
        "- 回应：‘听起来这段时间的工作让你感到非常疲惫和挫败，换做是谁可能都会觉得难以承受。’"
    ),
    Strategy.EXPLORATION: (
        "【策略：深度探索】\n"
        "目标：挖掘情绪背后的深层原因和认知。\n"
        "执行原则：使用开放式提问，鼓励用户叙述细节。\n"
        "示例：\n"
        "- 用户：‘我总觉得和大家格格不入。’\n"
        "- 回应：‘这种“格格不入”的感觉，通常会在什么场景下变得特别强烈？当时你的脑海里会浮现什么念头吗？’"
    ),
    Strategy.GENTLE_EXPLORATION: (
        "【策略：温和试探】\n"
        "目标：针对敏感或内向用户，在不给压力的前提下建立连接。\n"
        "执行原则：语句简洁、留白多、语气极度柔软，允许用户不回答。\n"
        "示例：\n"
        "- 用户：‘……没什。’\n"
        "- 回应：‘没关系的，如果你现在还没准备好开口，我们就这样安静地待一会儿也很好。’"
    ),
    Strategy.CBT_REFRAME: (
        "【策略：认知重构】\n"
        "目标：挑战非理性信念，寻找替代性视角。\n"
        "执行原则：识别“灾难化”或“全或无”思维，引导逻辑辩证。\n"
        "示例：\n"
        "- 用户：‘这次面试搞砸了，我这辈子都没希望了。’\n"
        "- 回应：‘一次面试的表现确实令人沮丧，但我们试着看一看，除了“没希望”，是否还有其他可能性？比如这仅仅是一次经验积累？’"
    ),
    Strategy.SUPPORT: (
        "【策略：支持与危机干预】\n"
        "目标：提供即时的心理稳态，确保用户安全。\n"
        "执行原则：坚定、温暖、提供力量感，弱化探索，强化“我在”。\n"
        "示例：\n"
        "- 用户：‘我真的撑不下去了。’\n"
        "- 回应：‘我能感受到你现在的痛苦已经到了极限。请记住，你不是一个人在面对，我会一直陪着你。’"
    ),
    Strategy.GUIDANCE: (
        "【策略：技巧指导】\n"
        "目标：提供具体的调适工具，增强效能感。\n"
        "执行原则：建议而非命令，解释原理，鼓励尝试。\n"
        "示例：\n"
        "- 用户：‘我心慌得厉害。’\n"
        "- 回应：‘这时候我们可以尝试一个“4-7-8呼吸法”：吸气4秒，憋气7秒，呼气8秒。这能通过生理调节帮助你的神经系统冷静下来。’"
    ),
}

def _get_emotion_strategy(emotion: str) -> str:
    """根据情绪类型返回策略"""
    emotion_map = {
        "焦虑": Strategy.CBT_REFRAME,
        "抑郁": Strategy.EXPLORATION,
        "愤怒": Strategy.EMPATHY,
        "恐惧": Strategy.GENTLE_EXPLORATION,
        "悲伤": Strategy.EMPATHY,
        "羞耻": Strategy.GENTLE_EXPLORATION,
        "内疚": Strategy.CBT_REFRAME,
        "孤独": Strategy.EXPLORATION,
        "绝望": Strategy.SUPPORT,
        "无助": Strategy.SUPPORT,
    }
    return emotion_map.get(emotion, "")

def _decide_strategy(
    emotion: str,
    intensity: str,
    risk_level: str,
    profile: Dict[str, Any],
) -> str:
    """核心决策逻辑"""
    # 1. 高风险优先
    if risk_level == "high":
        return Strategy.SUPPORT

    # 2. 中等风险
    if risk_level == "medium":
        return Strategy.EMPATHY

    # 3. 情绪导向优先
    emotion_strategy = _get_emotion_strategy(emotion)
    if emotion_strategy:
        return emotion_strategy

    # 4. 人格适配
    personality = profile.get("personality", [])
    communication_style = profile.get("communication_style", [])

    # 内向/敏感/被动 -> 温和探索
    introverted_traits = {"内向", "害羞", "保守", "敏感", "被动"}
    if any(trait in personality for trait in introverted_traits) or \
       any(trait in communication_style for trait in introverted_traits) or \
       "不愿主动表达" in communication_style:
        return Strategy.GENTLE_EXPLORATION

    # 5. 强度适配
    if intensity == "高":
        return Strategy.EMPATHY
    elif intensity == "低":
        return Strategy.GUIDANCE

    # 默认
    return Strategy.EMPATHY

def policy_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    策略决策节点入口函数
    """
    emotion = state.get("emotion", "")
    intensity = state.get("intensity", "中")
    risk_level = state.get("risk_level", "low")
    profile = state.get("profile", {})

    strategy = _decide_strategy(emotion, intensity, risk_level, profile)
    instruction = STRATEGY_INSTRUCTIONS.get(strategy, "")

    return {
        "strategy": strategy,
        "strategy_instruction": instruction,
    }

# 为了保持兼容性的便捷函数
def decide_strategy(
    emotion: str,
    intensity: str,
    risk_level: str,
    profile: Dict[str, Any],
) -> Tuple[str, str]:
    """便捷函数：返回策略名称和优化后的指令"""
    strategy = _decide_strategy(emotion, intensity, risk_level, profile)
    instruction = STRATEGY_INSTRUCTIONS.get(strategy, "")
    return strategy, instruction