"""LLM客户端封装"""
import os
from typing import Optional, List, Dict, Any


class LLMClient:
    """统一LLM调用接口"""

    def __init__(
        self,
        model_provider: str = "dashscope",
        model_name: str = "qwen-max",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        初始化LLM客户端

        Args:
            model_provider: 模型提供商 (dashscope/openai/local)
            model_name: 模型名称
            api_key: API密钥
            base_url: 自定义API地址（用于本地模型）
        """
        self.model_provider = model_provider
        self.model_name = model_name
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "YOUR_API_KEY_HERE")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        调用LLM生成回复

        Args:
            messages: 消息列表 [{"role": "user/assistant", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            LLM生成的文本
        """
        if self.model_provider == "dashscope":
            return self._call_dashscope(messages, temperature, max_tokens)
        elif self.model_provider == "openai":
            return self._call_openai(messages, temperature, max_tokens)
        elif self.model_provider == "local":
            return self._call_local(messages, temperature, max_tokens)
        else:
            raise ValueError(f"Unknown model provider: {self.model_provider}")

    def _call_dashscope(self, messages: List[Dict], temperature: float, max_tokens: int) -> str:
        """调用DashScope API（阿里云）"""
        from dashscope import Generation

        response = Generation.call(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=self.api_key,
            result_format='message'
        )
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            raise Exception(f"DashScope API error: {response.code} - {response.message}")

    def _call_openai(self, messages: List[Dict], temperature: float, max_tokens: int) -> str:
        """调用OpenAI API"""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Please install openai: pip install openai")

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        response = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def _call_local(self, messages: List[Dict], temperature: float, max_tokens: int) -> str:
        """调用本地模型（支持Ollama）"""
        if not self.base_url:
            raise ValueError("Local model requires base_url")

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Please install openai: pip install openai")

        client = OpenAI(api_key=self.api_key or "ollama", base_url=self.base_url)
        response = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content


def get_default_client() -> LLMClient:
    """获取默认LLM客户端"""
    return LLMClient(
        model_provider="dashscope",
        model_name="qwen-max",
    )