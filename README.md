# CBT 心理咨询 Agent (LangGraph版)

基于认知行为疗法(CBT)的心理咨询对话Agent，采用LangGraph工作流架构实现。

## 项目概述

本项目实现了一个AI心理咨询助手，遵循认知行为疗法(CBT)的基本原则，通过识别和质疑用户的负面思维模式来帮助改善情绪。

### 核心特性

- **LangGraph工作流**: 采用状态图架构，清晰定义对话流程
- **RAG知识检索**: 结合心理咨询知识库进行专业回答
- **多级安全机制**: 风险评估、高危识别、敏感内容过滤
- **记忆系统**: 短期对话记忆 + 长期记忆 + 用户画像

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      LangGraph Workflow                      │
├─────────────────────────────────────────────────────────────┤
│  memory → perception → router → rag → policy → generator    │
│                                    ↓                         │
│                              reviewer → safety → output      │
└─────────────────────────────────────────────────────────────┘
```

### 模块说明

| 模块 | 功能 |
|------|------|
| `graph/` | LangGraph工作流定义 |
| `memory/` | 记忆系统（短期/长期/画像） |
| `rag/` | RAG检索模块 |
| `generator/` | 回复生成器 |
| `safety/` | 安全检查与风险评估 |
| `utils/` | LLM客户端封装 |
| `config/` | 配置管理 |


### 核心依赖

- `langgraph` - 工作流框架
- `chromadb` - 向量数据库
- `dashscope` - 阿里云LLM服务(Qwen-Max)
- `streamlit` - Web界面

### 环境变量

```bash
export DASHSCOPE_API_KEY="your-api-key"
```

## 使用方式

### 1. 命令行交互

```bash
python main.py
```

命令:
- 输入内容与Agent对话
- `reset` - 重置记忆
- `summary` - 查看记忆摘要
- `quit` - 退出

### 2. Web界面

```bash
streamlit run main_page.py
```

提供图形化界面，支持对话历史、记忆重置、记忆摘要查看。

## 知识库

知识库目录: `./data`

可使用 `update_data.py` 更新知识库内容。

## 风险提示

⚠️ 本工具仅供心理科普使用，不可替代专业医疗建议。如有严重心理问题，请咨询专业心理医生或医疗机构。

## 目录结构

```
.
├── main.py              # 命令行入口
├── main_page.py        # Web界面入口
├── graph/              # LangGraph工作流
│   ├── graph.py        # 图定义与运行器
│   ├── state.py        # 状态定义
│   └── nodes/          # 节点实现
├── memory/             # 记忆系统
├── rag/                # RAG检索
├── generator/          # 回复生成
├── safety/             # 安全检查
├── utils/              # 工具模块
├── config/             # 配置
├── data/               # 知识库数据
└── memory_data.json   # 记忆存储
```

## License

MIT License