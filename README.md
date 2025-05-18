# Think Twice 🤔💡

**一个旨在提升您思考深度与提问效能的智能伙伴，助您开启更高质量的AI交互。采用FastAPI后端（支持Ollama, Gemini, 通义千问）与React前端架构。**

---

## 🌟 项目简介 (Introduction)

`Think Twice` 不仅仅是一个提示词优化工具，更是一个旨在提升您**思考深度**与**提问效能**的智能伙伴。我们坚信，卓越的AI交互源于清晰的自我认知和精准的沟通表达。

本项目的核心理念在于双重赋能：

1.  **深化您的思考，完善自身思路：**
    `Think Twice` 会引导您梳理、审视并拓展您最初的想法。它像一位循循善诱的导师，通过启发式的交互（未来功能），帮助您更清晰地定义自己的需求、目标以及期望从AI那里获得的具体成果。这个过程本身就是一次宝贵的思维锻炼，让您对所探寻的问题有更透彻的理解。

2.  **优化您的提问，赋能AI交互：**
    在您对自身需求有了更深刻的把握之后，`Think Twice` 会运用先进的提示工程策略，将您初步的、可能还略显模糊的构思，转化为结构清晰、意图明确、信息完备、且易于大型语言模型（LLM）或其他AI服务理解并高效执行的优质提示词。

通过这一“先内观、再外求”的协同过程，`Think Twice` 致力于帮助您充分解锁AI的潜能，开启更高质量、更富洞察力的AI对话，最终获取远超预期的成果。无论您是AI领域的新手，还是经验丰富的探索者，我们都希望能为您提供有力的支持，让每一次与AI的互动都深思熟虑，事半功倍。

## ✨ MVP核心功能 (Current MVP Features)

* **初步提示词优化 (P1 Generation)：** 根据用户输入的原始请求和选择的任务类型，通过配置的LLM服务（Ollama, Google Gemini, 或通义千问）生成一个初步优化后的提示词。
* **任务类型选择：** 用户可以在输入界面选择不同的任务类型，以获得更有针对性的优化。
* **用户友好的Web界面：** 基于React构建的现代化、简洁的前端用户界面。
* **可中止的请求：** 在AI处理请求时，用户可以点击停止按钮中止前端的等待。
* **(后端) AI辅助解释功能的核心逻辑：** 已经实现了通过API解释提示词中特定术语的后端能力（前端集成待完成）。
* **(后端) 结构化评估报告：** 评估LLM现在会输出结构化的JSON报告（前端利用待完成）。
* **多LLM后端支持：** 目前已集成Ollama（本地）、Google Gemini API和通义千问API，可通过配置切换。

## 🎯 目标用户 (Target Audience)

本项目面向所有对提升与大型语言模型交互效率和质量感兴趣的人，包括但不限于：

* 内容创作者
* 开发者与程序员
* 研究人员与学生
* 产品经理与设计师
* 任何希望通过AI提升工作效率和创造力的个人

## 🛠️ 技术栈 (Tech Stack)

* **后端 (Backend)：**
    * Python
    * FastAPI (用于构建API服务)
    * Pydantic (用于数据验证)
    * LLM服务集成:
        * Ollama (本地运行)
        * Google Generative AI SDK (Gemini API)
        * DashScope SDK (通义千问 API)
    * PDM (用于Python包和依赖管理)
* **前端 (Frontend)：**
    * React (使用 TypeScript 和 Vite)
    * CSS (用于样式)
* **版本控制：** Git & GitHub
* **单元测试：** Pytest (后端)

## 🚀 安装与运行 (Installation & Setup for MVP)

**重要提示：** 根据您选择的 `ACTIVE_LLM_PROVIDER`，您可能需要配置相应的API密钥或本地服务。

### A. 通用设置

1.  **克隆本仓库 (如果您尚未克隆)：**
    ```bash
    git clone [https://github.com/Yanxing-R/think-twice.git](https://github.com/Yanxing-R/think-twice.git) # 请确保这是您正确的仓库地址
    cd think-twice
    ```

2.  **配置环境变量 (`.env` 文件)：**
    在项目根目录下创建一个 `.env` 文件，并根据您希望使用的LLM服务添加相应的API密钥：
    ```env
    # .env 文件示例
    # DASHSCOPE_API_KEY="sk-your_qwen_api_key_here" # 通义千问API密钥 (SDK优先使用此变量名)
    # QWEN_API_KEY="sk-your_qwen_api_key_here"      # 也可作为备用
    
    # GEMINI_API_KEY="your_gemini_api_key_here"     # Google Gemini API密钥
    
    # ACTIVE_LLM_PROVIDER="qwen" # 设置激活的LLM服务: qwen, gemini, 或 ollama
    # QWEN_MODEL_NAME="qwen-plus" # 或您选择的通义模型
    # GEMINI_MODEL_NAME="gemini-1.5-flash-latest" # 或您选择的Gemini模型
    # OLLAMA_MODEL="qwen3:4b" # 或您选择的Ollama本地模型
    ```
    **确保将 `.env` 文件添加到 `.gitignore` 中，不要提交您的API密钥！**

### B. 后端 (FastAPI API服务)

1.  **确保PDM已安装并初始化项目：**
    参照 [PDM官方文档](https://pdm-project.org/) 安装PDM。
    在项目根目录下运行：
    ```bash
    pdm install
    ```
    这将安装所有Python依赖，包括 `fastapi`, `uvicorn`, `google-generativeai`, `dashscope`, `python-dotenv` 等。

2.  **如果您选择使用Ollama (`ACTIVE_LLM_PROVIDER="ollama"`)：**
    * 确保您的Ollama桌面应用正在运行，或已通过命令行启动Ollama服务。
    * 拉取您在 `settings.py` 或 `.env` 中配置的Ollama模型（例如 `ollama pull qwen3:4b`）。

3.  **启动FastAPI后端开发服务器：**
    在项目**根目录**下，运行以下命令：
    ```bash
    pdm run uvicorn src.meta_prompt_agent.api.main:app --reload --port 8000
    ```
    您应该会看到类似 `Uvicorn running on http://127.0.0.1:8000` 的输出。

### C. 前端 (React Web界面)

1.  **确保您已安装 Node.js 和 npm (或 yarn)。**

2.  **进入前端项目目录并安装依赖：**
    从项目**根目录**下，进入 `frontend` 文件夹：
    ```bash
    cd frontend
    npm install 
    # 或 yarn install
    ```

3.  **启动React前端开发服务器：**
    在 `frontend` 目录下，运行：
    ```bash
    npm run dev
    # 或 yarn dev
    ```
    这通常会在 `http://localhost:5173` 启动前端开发服务器。

## 💡 使用方法 (Usage - MVP)

1.  根据您在 `.env` 文件中配置的 `ACTIVE_LLM_PROVIDER`，确保相应的LLM服务（Ollama本地服务或云API密钥）已准备就绪。
2.  分别启动FastAPI后端服务器和React前端开发服务器。
3.  在浏览器中打开前端应用的地址（通常是 `http://localhost:5173`）。
4.  体验 "Think Twice"！

## 🤝 如何贡献 (Contributing)
# ... (保持不变，确保链接正确) ...

## 🗺️ 未来计划 (Roadmap)
# ... (请您整合您之前的更新和我们最新的讨论) ...
* **功能增强与智能化：**
    * [-] 引入更高级的提示词评估指标和反馈机制。(已实现结构化JSON评估后端)
    * [ ] **(下一步重点)** 在前端集成“AI辅助解释功能”。
    * [ ] 实现完整的人机协作元提示流程。
* **模型支持与灵活性：**
    * [-] 已支持Ollama, Gemini, 通义千问。
    * [ ] 增加更多模型选择和动态切换能力。
    * [ ] (长远) 提供“快/慢思考”模式。
* **用户体验与集成：**
    * [ ] 持续打磨和美化React前端UI/UX。
    * [ ] (长远) 实现更高级的定制化选项。
    * [ ] (长远) 针对特定高价值场景（PPT、视频脚本等）开发专门优化流程。
    * [ ] (长远) 提供API接口，使`Think Twice`能被其他应用或Agent调用。

## 📜 许可证 (License)

本项目采用 [MIT License](LICENSE) 开源许可证。

---

*如果您觉得这个项目对您有帮助，请给它一个 ⭐ Star！您的认可是我们持续改进的最大动力！*
