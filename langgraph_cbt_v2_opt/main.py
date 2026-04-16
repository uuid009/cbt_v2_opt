"""CBT心理Agent入口 - 使用LangGraph版本"""
import os
import sys

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.llm_client import LLMClient
from graph.graph import run_agent, get_graph
from memory.memory import Memory
from prompt_toolkit import prompt

def main():
    """主函数"""
    print("=" * 50)
    print("      心理学CBT Agent (LangGraph版)")
    print("=" * 50)
    print("使用说明:")
    print("  - 输入内容与Agent对话")
    print("  - 输入 'reset' 重置记忆")
    print("  - 输入 'summary' 查看记忆摘要")
    print("  - 输入 'quit' 退出")
    print("=" * 50)
    print()

    # 初始化LLM客户端
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    if api_key:
        print(f"使用DashScope API")
    else:
        print("警告: 未设置DASHSCOPE_API_KEY环境变量")
        print("请设置: export DASHSCOPE_API_KEY='your-api-key'")

    llm = LLMClient(
        model_provider="dashscope",
        model_name="qwen-max",
    )

    # 初始化memory实例（用于reset和summary）
    memory_storage = "./memory_data.json"
    memory = Memory()

    print("\n你好！我是心理咨询助手，有什么可以帮到你？\n")

    # 对话循环
    while True:
        try:
            user_input = prompt("你: ").strip()

            if not user_input:
                continue

            # 命令处理
            if user_input.lower() in ["quit", "exit", "退出"]:
                print("再见！保重。")
                break

            if user_input.lower() in ["reset", "重置"]:
                memory.clear()
                print("记忆已重置。\n")
                continue

            if user_input.lower() in ["summary", "摘要"]:
                print(memory.get_summary())
                continue

            # 正常对话 - 使用LangGraph
            response = run_agent(
                user_input,
                llm_client=llm,
                memory_storage=memory_storage,
                knowledge_dir="/home/lenovo/zch/Agent/data",
            )
            print(f"助手: {response}\n")

        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            print(f"错误: {e}")
            print("请重试或输入 'quit' 退出。\n")


if __name__ == "__main__":
    main()