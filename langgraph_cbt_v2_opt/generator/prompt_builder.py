"""Prompt构建器"""
from typing import Dict, Any, List


class PromptBuilder:
    """构建LLM prompt"""

    SYSTEM_PROMPT = """你是一位专业的心理咨询师，擅长使用CBT（认知行为疗法）技术帮助来访者。

核心原则：
1. 以来访者为中心，尊重其感受
2. 使用简洁、温暖、通俗易懂的语言
3. 适当使用CBT技术，但不要生硬套用
4. 保持专业边界，不提供诊断

注意事项：
- 长度控制在100-300字
- 避免说教或过于理论化
- 适当使用开放式问题引导思考
- 关注来访者的积极资源"""

    def build(
        self,
        user_input: str,
        state: Dict[str, Any],
        context: str,
        long_term: List[str],
        profile: Dict[str, Any],
        knowledge: List[str],
        strategy_instruction: str,
    ) -> List[Dict[str, str]]:
        """
        构建完整的prompt

        Args:
            user_input: 用户输入
            state: 状态 {"emotion", "intensity", "risk_level"}
            context: 短期对话上下文
            long_term: 长期记忆列表
            profile: 人格画像
            knowledge: RAG检索的知识
            strategy_instruction: 策略指令

        Returns:
            messages列表
        """
        # 构建用户当前状态部分
        state_section = self._build_state_section(state)

        # 构建对话上下文
        context_section = self._build_context_section(context)

        # 构建长期记忆
        long_term_section = self._build_long_term_section(long_term)

        # 构建人格画像
        profile_section = self._build_profile_section(profile)

        # 构建知识库
        knowledge_section = self._build_knowledge_section(knowledge)

        # 构建策略指令
        strategy_section = self._build_strategy_section(strategy_instruction)

        # 组合完整prompt
        user_content = f"""{state_section}

{context_section}

{long_term_section}

{profile_section}

{knowledge_section}

{strategy_section}

请根据以上信息生成回复："""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        return messages

    def _build_state_section(self, state: Dict[str, Any]) -> str:
        """构建状态部分"""
        emotion = state.get("emotion", "未知")
        intensity = state.get("intensity", "中")
        risk = state.get("risk_level", "low")

        return f"""【用户当前状态】
情绪：{emotion}
强度：{intensity}
风险等级：{risk}"""

    def _build_context_section(self, context: str) -> str:
        """构建对话上下文"""
        if not context or context == "（暂无对话历史）":
            return "【对话历史】无历史记录"
        return f"""【最近对话历史】
{context}"""

    def _build_long_term_section(self, long_term: List[str]) -> str:
        """构建长期记忆部分"""
        if not long_term:
            return "【长期了解】暂无"

        # 取最新的2-3条
        recent = long_term[-3:] if len(long_term) > 3 else long_term
        facts = "\n".join([f"- {fact}" for fact in recent])

        return f"""【对用户的长期了解】
{facts}"""

    def _build_profile_section(self, profile: Dict[str, Any]) -> str:
        """构建人格画像部分"""
        personality = profile.get("personality", [])
        communication_style = profile.get("communication_style", [])
        concerns = profile.get("concerns", [])

        parts = []
        if personality:
            parts.append(f"性格特点：{', '.join(personality[:5])}")
        if communication_style:
            parts.append(f"沟通风格：{', '.join(communication_style[:3])}")
        if concerns:
            parts.append(f"关注点：{', '.join(concerns[:3])}")

        if not parts:
            return "【用户特点】暂无明显特征"

        return f"""【用户特点】
{chr(10).join(parts)}"""

    def _build_knowledge_section(self, knowledge: List[str]) -> str:
        """构建知识库部分"""
        if not knowledge:
            return "【参考知识】无相关知识"

        # 取前2-3条
        selected = knowledge[:3] if len(knowledge) > 3 else knowledge
        items = "\n".join([f"- {item[:200]}" for item in selected])

        return f"""【心理学知识参考】
{items}"""

    def _build_strategy_section(self, strategy_instruction: str) -> str:
        """构建策略指令部分"""
        return f"""【本次回复策略】
{strategy_instruction}"""


# 便捷函数
def build_prompt(
    user_input: str,
    state: Dict[str, Any],
    context: str,
    long_term: List[str],
    profile: Dict[str, Any],
    knowledge: List[str],
    strategy_instruction: str,
) -> List[Dict[str, str]]:
    """便捷函数：构建prompt"""
    builder = PromptBuilder()
    return builder.build(
        user_input, state, context, long_term, profile, knowledge, strategy_instruction
    )


if __name__ == "__main__":
    # 测试
    builder = PromptBuilder()
    messages = builder.build(
        user_input="我最近工作压力很大",
        state={"emotion": "焦虑", "intensity": "中", "risk_level": "low"},
        context="用户：你好\n助手：你好",
        long_term=["用户工作压力较大", "用户经常加班"],
        profile={"personality": ["内向", "敏感"], "communication_style": ["不愿主动表达"]},
        knowledge=["焦虑的认知重构方法", "放松训练技巧"],
        strategy_instruction="请使用同理心回应",
    )

    for msg in messages:
        print(f"=== {msg['role'].upper()} ===")
        print(msg['content'][:500])
        print()