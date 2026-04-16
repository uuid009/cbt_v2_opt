import streamlit as st
import os
import sys
import time
from datetime import datetime

# 1. 确保可以导入项目模块 (假设此文件在项目根目录)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.llm_client import LLMClient
from graph.graph import run_agent
from memory.memory import Memory

# --- 页面配置 ---
st.set_page_config(
    page_title="CBT 心理咨询 Agent (LangGraph)",
    page_icon="🧠",
    layout="wide",
)

# --- 自定义样式 ---
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; }
    .sidebar-content { padding: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 初始化组件 (使用缓存避免重复初始化) ---
@st.cache_resource
def get_llm_client():
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    if not api_key:
        st.warning("⚠️ 未检测到 DASHSCOPE_API_KEY 环境变量")
    return LLMClient(
        model_provider="dashscope",
        model_name="qwen-max",
    )

@st.cache_resource
def get_memory_manager():
    # 这里的路径需与 run_agent 中的 memory_storage 保持一致
    memory_path = "./memory_data.json"
    return Memory()

llm = get_llm_client()
memory_manager = get_memory_manager()
KNOWLEDGE_DIR = "/home/lenovo/zch/Agent/data" # 对应你主程序中的路径
MEMORY_STORAGE = "./memory_data.json"

# --- 会话状态管理 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")

# --- 侧边栏：控制面板 ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3663/3663335.png", width=100)
    st.title("控制面板")
    st.markdown("---")
    
    st.info("💡 **提示**：本 Agent 基于认知行为疗法 (CBT) 设计，旨在通过识别负面思维模式来改善情绪。")
    
    # 功能按钮
    if st.button("🔄 重置对话记忆", use_container_width=True):
        memory_manager.clear()
        st.session_state.messages = []
        if "show_summary" in st.session_state:
            del st.session_state.show_summary
        st.success("记忆已成功重置")
        st.rerun()

    if st.button("📋 查看记忆摘要", use_container_width=True):
        summary = memory_manager.get_summary()
        print("Memory Summary:", summary)
        st.session_state.show_summary = summary

    # 显示摘要
    if "show_summary" in st.session_state:
        with st.expander("当前心理画像摘要", expanded=True):
            st.write(st.session_state.show_summary)

    st.markdown("---")
    st.caption(f"Session: {st.session_state.session_id}")
    st.caption("Backend: LangGraph + Qwen-Max")

# --- 主界面 ---
st.title("🧠 CBT 心理健康助理")
st.markdown("---")

# 渲染历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 聊天输入
if prompt_input := st.chat_input("分享你现在的感受..."):
    # 1. 展示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt_input})
    with st.chat_message("user"):
        st.markdown(prompt_input)

    # 2. 调用 LangGraph Agent
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("正在思考..."):
            try:
                # 调用你 graph.py 中的 run_agent 函数
                full_response = run_agent(
                    prompt_input,
                    llm_client=llm,
                    memory_storage=MEMORY_STORAGE,
                    knowledge_dir=KNOWLEDGE_DIR,
                )
                
                # 模拟流式打字效果
                displayed_text = ""
                for char in full_response:
                    displayed_text += char
                    message_placeholder.markdown(displayed_text + "▌")
                    time.sleep(0.01)
                message_placeholder.markdown(full_response)
                
                # 保存记忆
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                st.error(f"运行出错: {str(e)}")

# --- 页脚 ---
st.markdown("---")
st.caption("⚠️ 免责声明：本工具仅供心理科普使用，不可替代专业医疗建议。")