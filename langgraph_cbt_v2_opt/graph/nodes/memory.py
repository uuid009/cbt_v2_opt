"""
记忆节点 - 管理短期记忆、长期记忆和人格画像
"""
from typing import Dict, Any, List
from datetime import datetime

# 导入现有的Memory模块
from memory.memory import Memory


def memory_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    记忆节点 - 获取当前上下文

    Args:
        state: 当前状态

    Returns:
        更新后的状态（包含记忆）
    """
    # 获取memory实例
    memory = state.get("memory")
    print(f"[DEBUG memory_node] state.get('memory') = {memory}")
    print(f"[DEBUG memory_node] memory id = {id(memory) if memory else None}")
    if memory is None:
        storage_path = state.get("memory_storage", "./memory_data.json")
        memory = Memory()
        print(f"[DEBUG memory_node] Created NEW memory instance, id = {id(memory)}")

    # 获取短期对话
    short_term = memory.data.get("short_term", [])
    print(f"[DEBUG memory_node] short_term items: {len(short_term)}")
    for i, item in enumerate(short_term):
        print(f"  [{i}] user={item.get('user', '')[:30]}... pending={item.get('pending')} assistant={'yes' if item.get('assistant') else 'no'}")

    # 转换为消息格式
    messages = []
    for item in short_term[-10:]:  # 最近10轮
        # 跳过pending的条目，它们会在下面单独处理，避免重复添加
        if item.get("pending"):
            print(f"[DEBUG memory_node] Skipping pending item: {item.get('user', '')[:30]}...")
            continue
        messages.append({"role": "user", "content": item.get("user", "")})
        if item.get("assistant"):
            messages.append({"role": "assistant", "content": item.get("assistant", "")})

    # 获取当前用户输入（pending条目）
    # add_user_input已经预先添加了用户输入到short_term，
    # 但assistant为空，所以需要手动添加当前用户输入到消息中
    current_user_input = state.get("user_input", "")
    print(f"[DEBUG memory_node] current_user_input: {current_user_input[:50]}...")
    if current_user_input:
        # 检查最后一条是否是当前输入且没有assistant
        if short_term and short_term[-1].get("user") == current_user_input and not short_term[-1].get("assistant"):
            print(f"[DEBUG memory_node] Adding current user input to messages (pending item)")
            # 当前用户的输入还没有回复，将其加入消息列表
            messages.append({"role": "user", "content": current_user_input})
            # 注意：不要添加assistant消息，因为回复还没生成
        else:
            print(f"[DEBUG memory_node] NOT adding current input - condition failed")
            print(f"  short_term exists: {bool(short_term)}")
            if short_term:
                print(f"  short_term[-1].user == current_user_input: {short_term[-1].get('user') == current_user_input}")
                print(f"  not short_term[-1].get('assistant'): {not short_term[-1].get('assistant')}")

    print(f"[DEBUG memory_node] Final messages count: {len(messages)}")
    for i, msg in enumerate(messages):
        print(f"  [{i}] {msg['role']}: {msg['content'][:50]}...")

    # 获取长期记忆
    long_term = memory.get_long_term()

    # 获取人格画像
    profile = memory.get_profile()

    # 更新状态
    return {
        "short_term": messages,
        "long_term": long_term,
        "profile": profile,
    }


def update_memory_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    记忆更新节点 - 在回复后更新记忆

    Args:
        state: 当前状态

    Returns:
        更新后的状态
    """
    user_input = state.get("user_input", "")
    response = state.get("response", "")
    emotion = state.get("emotion", "")

    # print(f"[DEBUG update_memory_node] user_input: {user_input[:50]}...")
    # print(f"[DEBUG update_memory_node] response: {response[:50] if response else 'None'}...")

    # 获取memory实例
    memory = state.get("memory")
    if memory is None:
        memory = Memory()

    # 准备状态信息
    state_info = {
        "emotion": emotion,
        "intensity": state.get("intensity", "中"),
        "risk_level": state.get("risk_level", "low"),
    }
    
    print(f"[DEBUG update_memory_node] state_info: {state_info}")

    # 获取LLM客户端
    llm = state.get("llm_client")

    # 更新记忆
    memory.update_after_response(user_input, response, state_info, llm)

    return {"conversation_turn": state.get("conversation_turn", 0) + 1}


def get_memory_summary_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """获取记忆摘要节点"""
    memory = state.get("memory")
    if memory is None:
        return {"response": "记忆未初始化"}

    summary = memory.get_summary()
    return {"response": summary}