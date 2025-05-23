# ��💰  DeepFund 🔥🔥

**近期主要更新 (截至 2025-05-20):**

本项目近期进行了一系列重要更新基于DeepFund基线模型，旨在增强其分析能力、支持历史回测，并为未来的前端交互界面奠定基础。主要变更包括：

*   **核心分析流程重构 (`src/main.py`)**:
    *   将单日分析逻辑提取到可复用的 `run_single_day_analysis` 函数中，便于程序化调用和批量处理。
*   **历史分析数据生成 (`src/generate_historical_analysis.py`)**:
    *   新增脚本，用于批量执行指定日期范围内的每日分析，并将结果（包括分析师信号、决策、投资组合变动等）存入数据库。
    *   支持从特定配置启动，并能处理节假日，仅针对交易日进行分析。
*   **数据分析服务 (`src/analysis_service.py`)**:
    *   新增服务模块，提供 `get_historical_summary` 函数。
    *   该函数能从数据库中检索特定股票在指定实验配置和时间段内的所有分析师信号、决策，并（可选地，通过yfinance）整合股价信息。
    *   输出结构化的JSON，包含每日明细、整体趋势摘要和统计数据，为前端展示和API服务做好准备。
*   **配置和数据库工具更新 (`src/util/config.py`, `src/database/sqlite_helper.py`)**:
    *   `ConfigParser` 修改为可直接接受配置文件路径和交易日期字符串，以支持程序化调用。
    *   `sqlite_helper.py` 中增加了新的查询方法，如 `get_config_id_by_name`, `get_signals_for_ticker_period`, `get_decisions_for_ticker_period`，以支持上述服务的数据提取需求。相关的表结构和查询逻辑也进行了适配和优化。
*   **错误处理与健壮性**:
    *   增强了日期比较、API调用（如Alpha Vantage频率限制的识别）等方面的错误处理和日志记录。
*   **目标方向**:
    *   这些更新是为了将系统逐步改造为一个能够支持A股市场分析、提供历史趋势洞察，并最终通过前端界面展示实时买卖点建议的平台。

---

[![arXiv](https://img.shields.io/badge/arXiv-2503.18313-b31b1b.svg?style=flat)](https://arxiv.org/abs/2503.18313)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat)](https://www.python.org/downloads/release/python-3110/)

![Arena](./image/arena_v1.png)
> 🔔 Car-racing is for illustration only. Model performance is subject to the actual financial market.

This project serves as an ideal solution to the below key question:

### Will LLMs Be Professional At Fund Investment? 

We evaluate the trading capability of LLM across various financial markets given a unified environment. The LLM shall ingest external information, drive a multi-agent system, and make trading decisions. The LLM performance will be presented in a trading arena view across various dimensions. 

> 🔔 We are working on adding more particular analysts, extensive market and a front-end dashboard to deliver fresh insights. Welcome to collaborate with us!


## Disclaimer
This project is for educational and research purposes only, it **DOES NOT TRADE** actually.


## Framework
![Framework](./image/framework-v2.png)


## Setup Environment

1. Choose an environment manager:
   - If you want to use **Anaconda**: Install Conda (if not already installed): Go to [anaconda.com/download](https://www.anaconda.com/download/).
   - If you want to use **uv**: Install uv (if not already installed): Go to [uv installation guide](https://docs.astral.sh/uv/getting-started/installation).

2. Clone the repository:
```bash
git clone https://github.com/HKUSTDial/DeepFund.git
cd DeepFund
```

3. Create a virtual env from the env configuration file:
    1. If you are using **Anaconda**:
         ```bash
         conda env create -f environment.yml # if using Conda
         ```
    2. If you are using **uv**:
         ```bash
         uv sync # detects pyproject.toml, create an venv at project root, and install the dependencies
         source .venv/bin/activate # or .venv\Scripts\activate for windows to activate the venv
         ```

4. Set up environment variables:
```bash
# Create .env file for your API keys (OpenAI, DeepSeek, etc.)
cp .env.example .env
```

## Connect to Database
To better track the system performance, DeepFund uses a database to timely monitor the trading status. Besides, it also stores the LLM reasoning results for future analysis and traceback.

### Option 1: Use **Supabase**
DeepFund connects to Supabase **by default**. 
- Supabase is a PostgreSQL-compatible Cloud Database
- You can create a free account on [Supabase](https://supabase.com/) website.
- Refer to `src/database/supabase_setup.sql` to create the tables.
- Update the `SUPABASE_URL` and `SUPABASE_KEY` in `.env` file.

### Option 2: Use **SQLite**
SQLite is a lightweight database that stores data locally.
- Run the following command to **create a sqlite database** in the path
```bash
cd src
python database/sqlite_setup.py
```
- You may install VSCode Extension [SQLite Viewer](https://marketplace.cursorapi.com/items?itemName=qwtel.sqlite-viewer) to explore the database.
- Path: `src/assets/deepfund.db`
- Switch to local DB by adding `--local-db` option in the command line. 

### Relation Diagram
DeepFund system gets supported by four elementary tables: 
- Config: store user-defined configurations
- Portfolio: record the portfolio updates
- Decision: record the trading decisions from managers
- Signal: record the signals generated from analysts

The ERD is generated by Supabase - DB Schema Visualizer.

<p align="center">
  <img src="./image/db_schema.gif" alt="DeepFund ERD" width="80%" />
  <br>
</p>


## Running the System
Enter the `src` directory and run the `main.py` file with configuration:
```bash
cd src
python main.py --config xxx.yaml --trading-date YYYY-MM-DD [--local-db]
```

`trading-date` coordinates the trading date for the system. It can be set to historical trading date till the last trading date. As the portfolio is updated daily, client must use it in **chronological order** to replay the trading history.

### Configurations
Configs are saved in `src/config`. Below is a config template:
```yaml
# Deep Fund Configuration
exp_name: "my_unique_exp_name"

# Trading settings
tickers:
  - ticker_a
  - ticker_b

# Analysts to run, refer to graph.constants.py
planner_mode: true/false
workflow_analysts:
  - analyst_a
  - analyst_b
  - analyst_c

# LLM model settings, refer to llm/inference.py
llm:
  provider: "provider_name" 
  model: "model_name"
```


### Planner Mode
We use `planner_mode` configs to switch the mode:
- **True**: Planner agent orchestrates which analysts to run from `workflow_analysts`.
- **False**: All workflow analysts are running in parallel without orchestration.

### Remarks
- `exp_name` is **unique identifier** for each experiment. You shall use another one for different experiments when configs are changed.
- Specify `--local-db` flag to use SQLite. Otherwise, DeepFund connects to Supabase by default.


## Project Structure 
```
deepfund/
├── src/
│   ├── main.py                   # Main entry point
│   ├── agents/                   # Agent build and registry
│   ├── apis/                     # APIs for external financial data
│   ├── config/                   # Configuration files
│   ├── database/                 # Database setup and helper
│   ├── example/                  # Expected output
│   ├── graph/                    # Workflow, prompt, and schema
│   ├── llm/                      # LLM providers
│   ├── util/                     # Utility functions and helpers
├── environment.yml               # For Conda
├── README.md                     # Project documentation
├── ...
```

##  Analyst Breakdown

|    Name     |   Function  | Upstream Source | 
| ----------- | ----------- | ----------- | 
| company_news  | Analyzes company news. | Lately Company news.  | 
| fundamental   | Analyzes financial metrics. | Company profitability, growth, cashflow and financial health. |
| insider       | Analyzes company insider trading activity. | Recent insider transactions made by key stakeholders. |
| macroeconomic | Analyzes macroeconomic indicators. | US economic indicators GDP, CPI, rate, unemployment, etc.    |
| policy        | Analyzes policy news. | Fiscal and monetary policy news. |
| technical     | Analyzes technical indicators  for short to medium-term price movement predictions. | Technical indicators trend, mean reversion, RSI, volatility, volume, support resistance. |

#### Remarks:
**Unified Output**: All analysts output the same format: Signal=(Bullish, Bearish, Neutral), Justification=...

**Time-sensitive Analysts**: Because of the constraints of upstream API service, analyst **company_news**, **insider**, **policy**, and **technical** support  historical data analysis via `trading-date` option, while other analysts can only retrieve the latest data.


## System Dependencies

### LLM Providers
- Official API: OpenAI, DeepSeek, Anthropic, Grok, etc.
- LLM Proxy API: Fireworks AI, AiHubMix, etc.
- Local API: Ollama, etc.

### Financial Data Source 
- Alpha Vantage API: Stock Market Data API, [Claim Free API Key](https://www.alphavantage.co)
- YFinance API: Download Market Data from Yahoo! Finance's API, [Doc](https://yfinance-python.org/)


## Advanced Usage
### How to add a new analyst?

To add a new analyst to the DeepFund system, follow these general steps:

1.  **Build the Analyst:**
    Create a new Python file for your analyst within the `src/agents/analysts` directory. Implement the core logic for your analyst within this file. This typically involves defining an agent function that takes relevant inputs (like tickers, market data), performs analysis (potentially using LLMs or specific APIs), and returns signals.

2.  **Define Prompts:**
    If your analyst is driven by an LLM, define the prompt(s) it will use. These will go in the `src/llm/prompt.py` file.

3.  **Register the Analyst:**
    Make the system aware of your new analyst. This will involve adding its name or reference to a central registry in `src/graph/constants.py` or within the agent registration logic in `src/agents/registry.py`. Check these files for patterns used by existing analysts.

4.  **Update Configuration:**
    Add the unique name or key of your new analyst to the `workflow_analysts` list in your desired configuration file (e.g., `src/config/my_config.yaml`).

5.  **Add Data Dependencies (if any):**
    If your analyst requires new external data sources (e.g., a specific API), add the necessary API client logic in the `src/apis/` directory, and update environment variable handling (`.env.example`, `.env`) if API keys are needed.

6.  **Testing:**
    Thoroughly test your new analyst by running the system with a configuration that includes it. Check the database tables (`Decision`, `Signal`) to ensure it produces the expected output and integrates correctly with the portfolio manager.

Remember to consult the existing analyst implementations in `src/agents/` and the workflow definitions in `src/graph/` for specific patterns and conventions used in this project.

---

### How to add a new base LLM?

To integrate a new LLM provider (e.g., a different API service) into the system:

1.  **Implement Provider Logic:**
    Please refer to `src/llm/new_provider.py` for the implementation. We align the structure of the new provider with the existing providers.

2.  **Handle API Keys:**
    If the new provider requires an API key or other credentials, add the corresponding environment variable(s) to `.env.example` and instruct users to add their keys to their `.env` file.

3.  **Update Configuration:**
    Document the necessary `provider` and `model` names for the new service. Users will need to specify these in their YAML configuration files under the `llm:` section (e.g., in `src/config/provider/my_config.yaml`).
    ```yaml
    llm:
      provider: "" # The identifier you added in step 1
      model: "" # provider-specific settings here
    ```

4.  **Testing:**
    Run the system using a configuration file that specifies your new LLM provider. Ensure that the LLM calls are successful and that the agents receive the expected responses.

Consult the implementations for existing providers (like OpenAI, DeepSeek) in `src/llm/` as a reference.



## Acknowledgements
The project gets inspiration and supports from the following projects:
- [AI Hedge Fund](https://github.com/virattt/ai-hedge-fund), An AI Hedge Fund Team
- [LangGraph](https://langchain-ai.github.io/langgraph/tutorials/workflows), Tutorial on Workflows and Agents
- [OpenManus](https://github.com/mannaandpoem/OpenManus), An open-source framework for building general AI agents
- [Supabase](https://supabase.com/), The Open Source Firebase Alternative
- [Cursor AI](https://www.cursor.com/), The AI Code Editor


## Citation
If you find this project useful, please cite it as follows:
```bibtex
@misc{li2025deepfund,
      title={DeepFund: Will LLM be Professional at Fund Investment? A Live Arena Perspective}, 
      author={Changlun Li and Yao Shi and Yuyu Luo and Nan Tang},
      year={2025},
      eprint={2503.18313},
      archivePrefix={arXiv},
      primaryClass={cs.MA},
      url={https://arxiv.org/abs/2503.18313}, 
}
```

# DeepFund Trading System

**近期主要更新 (截至 YYYY-MM-DD):**

本项目近期进行了一系列重要更新，旨在增强其分析能力、支持历史回测，并为未来的前端交互界面奠定基础。主要变更包括：

*   **核心分析流程重构 (`src/main.py`)**:
    *   将单日分析逻辑提取到可复用的 `run_single_day_analysis` 函数中，便于程序化调用和批量处理。
*   **历史分析数据生成 (`src/generate_historical_analysis.py`)**:
    *   新增脚本，用于批量执行指定日期范围内的每日分析，并将结果（包括分析师信号、决策、投资组合变动等）存入数据库。
    *   支持从特定配置启动，并能处理节假日，仅针对交易日进行分析。
*   **数据分析服务 (`src/analysis_service.py`)**:
    *   新增服务模块，提供 `get_historical_summary` 函数。
    *   该函数能从数据库中检索特定股票在指定实验配置和时间段内的所有分析师信号、决策，并（可选地，通过yfinance）整合股价信息。
    *   输出结构化的JSON，包含每日明细、整体趋势摘要和统计数据，为前端展示和API服务做好准备。
*   **配置和数据库工具更新 (`src/util/config.py`, `src/database/sqlite_helper.py`)**:
    *   `ConfigParser` 修改为可直接接受配置文件路径和交易日期字符串，以支持程序化调用。
    *   `sqlite_helper.py` 中增加了新的查询方法，如 `get_config_id_by_name`, `get_signals_for_ticker_period`, `get_decisions_for_ticker_period`，以支持上述服务的数据提取需求。相关的表结构和查询逻辑也进行了适配和优化。
*   **错误处理与健壮性**:
    *   增强了日期比较、API调用（如Alpha Vantage频率限制的识别）等方面的错误处理和日志记录。
*   **目标方向**:
    *   这些更新是为了将系统逐步改造为一个能够支持A股市场分析、提供历史趋势洞察，并最终通过前端界面展示实时买卖点建议的平台。

---
