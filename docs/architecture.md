# 项目架构概览

本文档旨在提供 `meta-prompt-agent` 项目的高层次架构概览，重点描述主要目录结构和关键模块的职责。

## 1. 顶层目录结构


meta-prompt-agent/
├── .git/                     # Git 版本控制元数据
├── .venv/                    # PDM 管理的 Python 虚拟环境 (被 .gitignore 忽略)
├── docs/                     # 项目文档 (例如本架构文档)
│   └── architecture.md
├── src/                      # 主要的 Python 源代码
│   └── meta_prompt_agent/    # 项目的核心 Python 包
├── tests/                    # 自动化测试代码
│   ├── unit/                 # 单元测试
│   └── integration/          # (预留) 集成测试
├── .gitignore                # Git 忽略规则
├── LICENSE                   # 项目开源许可证
├── README.md                 # 项目入口文档，包含简介、安装、使用等
├── pdm.lock                  # PDM 锁定的精确依赖版本
└── pyproject.toml            # 项目元数据及 PDM 依赖配置文件 (PEP 518, PEP 621)


## 2. 源代码 (`src/meta_prompt_agent/`)

所有核心的 Python 源代码都位于 `src/` 目录下的 `meta_prompt_agent` 包中。这种 `src` 布局有助于清晰地分离源代码和项目管理文件，并简化打包和分发。

### 2.1. `app/` - 用户界面层

* **职责：** 处理所有与用户界面（通过 Streamlit 构建）相关的逻辑。
* **关键文件：**
    * `main_ui.py`: Streamlit 应用的主入口点，负责渲染界面元素、处理用户输入和展示结果。它调用 `core` 层的服务来执行业务逻辑。
    * `components/` (可选): 如果未来UI组件变得复杂，可复用的UI片段可以组织在这里。

### 2.2. `core/` - 核心业务逻辑层

* **职责：** 实现项目的主要业务功能，即元提示的生成、评估和精炼。
* **关键文件：**
    * `agent.py`: 包含核心的 `generate_and_refine_prompt` 函数，负责编排整个提示优化流程，包括调用LLM接口、处理结构化模板、执行自我校正循环等。它也可能包含如 `load_feedback`, `save_feedback` 等辅助业务逻辑。
    * `llm_interface.py` (规划中/部分实现于 `agent.py`): 专门负责与底层大型语言模型（如通过 Ollama）进行交互的模块。它的目标是封装API调用的细节，为 `agent.py` 提供一个清晰的接口。目前，这部分逻辑主要在 `call_ollama_api` 函数中，位于 `agent.py`。
    * `feedback_manager.py` (规划中/部分实现于 `agent.py`): 专门负责加载和保存用户反馈数据的模块。目前，这部分逻辑是 `load_feedback` 和 `save_feedback` 函数，位于 `agent.py`。

### 2.3. `prompts/` - 提示词模板管理

* **职责：** 存放和管理所有用于元提示工程的模板字符串和结构化模板定义。
* **关键文件：**
    * `templates.py`: 定义了如 `CORE_META_PROMPT_TEMPLATE`、`EVALUATION_META_PROMPT_TEMPLATE`、`REFINEMENT_META_PROMPT_TEMPLATE` 以及 `STRUCTURED_PROMPT_TEMPLATES` 字典等。

### 2.4. `config/` - 配置管理

* **职责：** 集中管理项目的配置参数。
* **关键文件：**
    * `settings.py`: 定义项目运行所需的配置变量，例如 Ollama 模型的名称 (`OLLAMA_MODEL`)、API 地址 (`OLLAMA_API_URL`)、反馈文件名 (`FEEDBACK_FILE`) 等。
    * `logging_config.py`: 包含 `setup_logging` 函数，用于在应用启动时统一配置日志系统。

### 2.5. `utils/` - 通用工具模块 (可选)

* **职责：** 存放项目中可能被多个模块复用的通用辅助函数或类（例如，特殊的文本处理工具、日期时间函数等）。目前项目中可能尚未显式使用此目录。

### 2.6. `__init__.py`

* 在 `meta_prompt_agent/` 及其各子目录中，`__init__.py` 文件（即使为空）将这些目录标记为 Python 的包或模块，使得它们可以被正确导入。

## 3. 测试 (`tests/`)

* **职责：** 包含所有的自动化测试代码，以确保代码质量和功能的正确性。
* **子目录：**
    * `unit/`: 存放单元测试，针对项目中最小的可测试单元（函数、方法）进行测试。例如，`test_agent.py` 包含了对 `core/agent.py` 中函数的测试。
    * `integration/` (预留): 未来可以用于存放集成测试，测试多个模块协同工作的场景。

## 4. 主要数据流 (简要)

1.  用户通过 `app/main_ui.py` 提供的 Streamlit 界面输入原始请求和配置。
2.  `main_ui.py` 调用 `core/agent.py` 中的 `generate_and_refine_prompt` 函数。
3.  `generate_and_refine_prompt`：
    * 根据用户选择和任务类型，可能调用 `prompts/templates.py` 中的模板和 `core/agent.py` 中的 `load_and_format_structured_prompt` 来构建初始核心提示。
    * 多次调用 `core/agent.py` 中的 `call_ollama_api`（它内部使用 `config/settings.py` 中的配置）与Ollama服务交互，以获取优化提示、评估报告和精炼提示。
    * 将最终结果返回给 `main_ui.py`。
4.  `app/main_ui.py` 将结果展示给用户。
5.  用户反馈通过 `app/main_ui.py` 收集，并调用 `core/agent.py` 中的 `save_feedback`（它使用 `config/settings.py` 中的 `FEEDBACK_FILE` 配置）进行保存。



