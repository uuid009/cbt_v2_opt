"""回复生成模块"""
from typing import Dict, Any, List
from utils.llm_client import LLMClient, get_default_client
from generator.prompt_builder import PromptBuilder
from config.config import config

class ResponseGenerator:
    """回复生成器"""

    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client or get_default_client()
        self.prompt_builder = PromptBuilder()

    def generate(
        self,
        user_input: str,
        state: Dict[str, Any],
        context: str,
        long_term: List[str],
        profile: Dict[str, Any],
        knowledge: List[str],
        strategy_instruction: str,
    ) -> str:
        """
        生成回复

        Args:
            user_input: 用户输入
            state: 状态
            context: 对话上下文
            long_term: 长期记忆
            profile: 人格画像
            knowledge: 知识
            strategy_instruction: 策略指令

        Returns:
            生成的回复
        """
        # 构建prompt
        messages = self.prompt_builder.build(
            user_input=user_input,
            state=state,
            context=context,
            long_term=long_term,
            profile=profile,
            knowledge=knowledge,
            strategy_instruction=strategy_instruction,
        )

        # 调用LLM
        response = self.llm.chat(
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

        return self._post_process(response)

    def _post_process(self, response: str) -> str:
        """后处理回复"""
        # 去除多余空白
        response = response.strip()

        # 确保不是空回复
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
    generator = ResponseGenerator(llm_client)
    return generator.generate(
        user_input,
        state,
        context,
        long_term,
        profile,
        knowledge,
        strategy_instruction,
    )


if __name__ == "__main__":
    # 测试
    from utils.llm_client import LLMClient

    llm = LLMClient()
    generator = ResponseGenerator(llm)

    response = generator.generate(
        user_input="我最近工作压力很大，晚上都睡不着",
        state={"emotion": "焦虑", "intensity": "中", "risk_level": "low"},
        context="用户：你好\n助手：你好，很高兴见到你",
        long_term=["用户工作压力较大", "用户提到睡眠不好"],
        profile={"personality": ["内向"], "communication_style": []},
        knowledge=["放松训练方法", "睡眠卫生建议"],
        strategy_instruction="请使用同理心回应",
    )

    print("生成的回复:")
    print(response)