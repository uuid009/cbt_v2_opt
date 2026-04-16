"""统一记忆模块 - 管理短期记忆、长期记忆和人格画像"""
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from config.config import config


class Memory:
    """统一记忆管理器"""

    def __init__(self):
        """
        初始化记忆管理器

        Args:
            storage_path: 记忆存储文件路径
            short_term_max: 短期记忆最大轮数
        """
        self.storage_path = config.storage_path
        self.short_term_max = config.short_term_max

        # 加载已有记忆
        self.data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        """加载记忆数据"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass

        # 默认结构
        return {
            "short_term": [],  # 短期对话
            "long_term": [],   # 长期记忆
            "profile": {        # 人格画像
                "personality": [],      # 性格标签
                "communication_style": [],  # 沟通风格
                "concerns": [],         # 关注点
                "risk_flag": "low",      # 风险标志
            },
            "last_updated": datetime.now().isoformat(),
        }

    def _save_data(self):
        """保存记忆数据"""
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    # ========== 获取方法 ==========

    def get_context(self) -> str:
        """获取短期对话上下文"""
        short_term = self.data.get("short_term", [])
        if not short_term:
            return "（暂无对话历史）"

        # 过滤掉已完成的条目（只有用户输入没有回复的）
        completed = [item for item in short_term if not item.get("pending")]

        # 构建上下文时，包含已完成的对话 + 当前pending的用户输入
        context_parts = []
        for item in completed[-10:]:  # 已完成的对话历史
            context_parts.append(f"用户: {item['user']}")
            context_parts.append(f"助手: {item['assistant']}")

        # 找出pending的条目（当前用户刚输入但还没回复的）
        pending_items = [item for item in short_term if item.get("pending")]
        if pending_items:
            # 添加当前用户输入到上下文中
            context_parts.append(f"用户: {pending_items[-1]['user']}")
            context_parts.append(f"助手: ")  # 等待回复

        return "\n".join(context_parts)

    def get_long_term(self) -> List[str]:
        """获取长期记忆"""
        return self.data.get("long_term", [])

    def get_profile(self) -> Dict[str, Any]:
        """获取人格画像"""
        return self.data.get("profile", {})

    # ========== 更新方法 ==========

    def add_user_input(self, user_input: str):
        """预先添加用户输入到短期记忆（用于解决回复延迟一轮的问题）"""
        short_term = self.data.get("short_term", [])

        # 添加一个只有用户输入的临时条目，等待assistant回复后更新
        short_term.append({
            "user": user_input,
            "assistant": "",  # 暂时为空，回复后填充
            "timestamp": datetime.now().isoformat(),
            "pending": True  # 标记为待完成
        })

        # 限制长度
        if len(short_term) > self.short_term_max:
            short_term = short_term[-self.short_term_max:]

        self.data["short_term"] = short_term
        # 必须立即保存，否则memory_node中的新Memory实例无法加载到pending项
        self._save_data()

    def update_after_response(
        self,
        user_input: str,
        assistant_response: str,
        state: Dict[str, Any],
        llm_client=None,
    ):
        """
        在回复生成后更新记忆（更新pending的条目，并抽取长期信息）

        Args:
            user_input: 用户输入
            assistant_response: 助手回复
            state: 当前状态 {"emotion", "intensity", "risk_level"}
            llm_client: LLM客户端（用于抽取长期信息）
        """
        # 1. 更新短期记忆中的pending条目
        short_term = self.data.get("short_term", [])
        if short_term and short_term[-1].get("pending") and short_term[-1]["user"] == user_input:
            short_term[-1]["assistant"] = assistant_response
            short_term[-1]["pending"] = False
        else:
            # 如果没有pending条目，直接添加
            short_term.append({
                "user": user_input,
                "assistant": assistant_response,
                "timestamp": datetime.now().isoformat(),
            })

        # 限制长度
        if len(short_term) > self.short_term_max:
            short_term = short_term[-self.short_term_max:]

        self.data["short_term"] = short_term

        # 2. 抽取并更新长期记忆
        self._update_long_term(user_input, state, llm_client)

        # 3. 更新人格画像
        self._update_profile(user_input, state, llm_client)

        # 4. 保存
        self._save_data()

    def update(
        self,
        user_input: str,
        assistant_response: str,
        state: Dict[str, Any],
        llm_client=None,
    ):
        """
        更新记忆（兼容旧接口）

        Args:
            user_input: 用户输入
            assistant_response: 助手回复
            state: 当前状态 {"emotion", "intensity", "risk_level"}
            llm_client: LLM客户端（用于抽取长期信息）
        """
        # 1. 更新短期记忆
        self._update_short_term(user_input, assistant_response)

        # 2. 抽取并更新长期记忆
        self._update_long_term(user_input, state, llm_client)

        # 3. 更新人格画像
        self._update_profile(user_input, state, llm_client)

        # 4. 保存
        self._save_data()

    def _update_short_term(self, user_input: str, assistant_response: str):
        """更新短期记忆"""
        short_term = self.data.get("short_term", [])

        short_term.append({
            "user": user_input,
            "assistant": assistant_response,
            "timestamp": datetime.now().isoformat(),
        })

        # 限制长度
        if len(short_term) > self.short_term_max:
            short_term = short_term[-self.short_term_max:]

        self.data["short_term"] = short_term

    def _update_long_term(
        self,
        user_input: str,
        state: Dict[str, Any],
        llm_client=None,
    ):
        """抽取并更新长期记忆"""
        long_term = self.data.get("long_term", [])

        # 使用LLM抽取关键信息
        if llm_client:
            try:
                prompt = f"""从以下用户输入中抽取可能对心理治疗有价值的关键信息（如生活事件、长期困扰、重要经历等）。

用户输入：{user_input}
当前情绪状态：{state.get('emotion', '未知')}

如果抽取到重要信息，返回JSON格式：{{"key_fact": "关键信息"}}
如果没有重要信息，返回：{{"key_fact": null}}"""

                result = llm_client.chat(
                    [{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=200,
                )

                import json as json_module
                import re
                match = re.search(r'\{[^}]+\}', result)
                if match:
                    parsed = json_module.loads(match.group())
                    key_fact = parsed.get("key_fact")
                    if key_fact and key_fact not in long_term:
                        # 避免重复
                        is_duplicate = any(key_fact in existing for existing in long_term)
                        if not is_duplicate:
                            long_term.append(key_fact)

                            # 限制长期记忆数量
                            if len(long_term) > 20:
                                long_term = long_term[-20:]
            except Exception as e:
                print(f"Long-term extraction error: {e}")

        self.data["long_term"] = long_term

    def _update_profile(
        self,
        user_input: str,
        state: Dict[str, Any],
        llm_client=None,
    ):
        """更新人格画像"""
        profile = self.data.get("profile", {})
        
        # 1. 更新风险标志
        current_risk = state.get("risk_level", "0")
        if current_risk == 0:
            profile["risk_flag"] = "low"
        if current_risk == 2:
            profile["risk_flag"] = "high"
        elif current_risk == 1 and profile.get("risk_flag") != 2:
            profile["risk_flag"] = "medium"

        # 2. 使用LLM抽取性格和沟通风格
        if llm_client:
            try:
                prompt = f"""分析以下用户输入，提取相关的性格特征和沟通风格标签。

用户输入：{user_input}

返回JSON格式：
{{
    "personality": ["性格标签1", "性格标签2"],
    "communication_style": ["沟通风格标签1"],
    "concerns": ["关注点1"]
}}

如果没有新信息，返回空数组。不要编造信息。"""

                result = llm_client.chat(
                    [{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=300,
                )

                import json as json_module
                import re
                match = re.search(r'\{[^}]+\}', result)
                if match:
                    parsed = json_module.loads(match.group())

                    # 更新性格标签
                    new_personality = parsed.get("personality", [])
                    if new_personality:
                        existing = set(profile.get("personality", []))
                        existing.update(new_personality)
                        profile["personality"] = list(existing)[:10]  # 限制数量

                    # 更新沟通风格
                    new_style = parsed.get("communication_style", [])
                    if new_style:
                        existing = set(profile.get("communication_style", []))
                        existing.update(new_style)
                        profile["communication_style"] = list(existing)[:5]

                    # 更新关注点
                    new_concerns = parsed.get("concerns", [])
                    if new_concerns:
                        existing = set(profile.get("concerns", []))
                        existing.update(new_concerns)
                        profile["concerns"] = list(existing)[:10]

            except Exception as e:
                print(f"Profile update error: {e}")

        self.data["profile"] = profile

    # ========== 管理方法 ==========

    def clear(self):
        """清空所有记忆"""
        self.data = {
            "short_term": [],
            "long_term": [],
            "profile": {
                "personality": [],
                "communication_style": [],
                "concerns": [],
                "risk_flag": "low",
            },
            "last_updated": datetime.now().isoformat(),
        }
        self._save_data()

    def get_summary(self) -> str:
        """获取记忆摘要（用于调试）"""
        self.data = self._load_data()
        profile = self.get_profile()
        return f"""
短期对话轮数: {len(self.data.get('short_term', []))}
长期记忆条数: {len(self.data.get('long_term', []))}
性格标签: {profile.get('personality', [])}
沟通风格: {profile.get('communication_style', [])}
关注点: {profile.get('concerns', [])}
风险标志: {profile.get('risk_flag', 'low')}
"""


# 便捷函数
def create_memory(storage_path: str = "./memory_data.json") -> Memory:
    """创建记忆管理器"""
    return Memory()


if __name__ == "__main__":
    # 测试
    mem = Memory("/home/lenovo/zch/Agent/langgraph_cbt_v1_simplify/memory_data.json")
    mem.update(
        "我最近工作压力很大，经常失眠",
        "听起来确实让人困扰，能具体说说吗？",
        {"emotion": "焦虑", "intensity": "中", "risk_level": "low"},
    )
    print(mem.get_summary())
    print("长期记忆:", mem.get_long_term())