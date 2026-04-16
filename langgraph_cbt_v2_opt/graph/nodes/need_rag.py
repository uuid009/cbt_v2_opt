from typing import Dict, Any
from utils.llm_client import LLMClient, get_default_client

def router_node(state: Dict[str, Any]) -> Dict[str, Any]:
    query = state["user_input"]
    llm = state["llm_client"]

    prompt = f"""
判断用户问题是否需要查询知识库：

问题：
{query}

规则：
1. 闲聊 / 问候 → NO
2. 通用心理问题（如“焦虑怎么办”）→ NO
3. 需要具体知识 / 外部资料 → YES

只输出 YES 或 NO
"""
    llm = get_default_client()
    resp = llm.chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    content = resp if isinstance(resp, str) else resp.content

    need_rag = "YES" in content.upper()

    
    print(f"need_rag: {need_rag}")
    return {"need_rag": need_rag}