# simple-agent-with-skills

基于 **Anthropic Messages API** 的最小异步 Agent 模板：环境变量管理密钥与 Base URL、工具调用循环、从目录加载 Markdown 技能、Typer CLI。不使用 LangChain。

## 功能概览

| 能力 | 说明 |
|------|------|
| 运行时 | **uv** 管理依赖与可编辑包 |
| API | `anthropic` 官方异步客户端 `AsyncAnthropic` |
| 配置 | `.env`：`ANTHROPIC_API_KEY`、`ANTHROPIC_BASE_URL`（可选）、`ANTHROPIC_MODEL`、`SKILLS_DIR` |
| 工具 | `tools.py` 中声明 JSON Schema + 本地执行函数，agent 内自动多轮 `tool_use` |
| 技能 | `skills/*.md` 全文注入 system prompt（可换目录） |
| CLI | `simple-agent-with-skills chat "你的问题"` |

## 快速开始

### 1. 安装依赖（uv）

```bash
cd /path/to/simple-agent-with-skills
uv sync
```

### 2. 配置密钥与网关

```bash
cp .env.example .env
# 编辑 .env：填写 ANTHROPIC_API_KEY；若使用代理/兼容 API，设置 ANTHROPIC_BASE_URL
```

- **`ANTHROPIC_BASE_URL`**：传给 `AsyncAnthropic(base_url=...)`，用于替换官方默认请求根地址（例如企业代理或兼容实现）。留空则使用 SDK 默认。
- `.env` 自动查找顺序：优先当前工作目录，其次项目根目录；也可用 `--env-file` 显式指定。

### 3. 运行

```bash
uv run simple-agent-with-skills chat "用工具计算 2.5 + 3.1，并简要说明"
```

排查鉴权或路径问题时可打开调试日志：

```bash
uv run simple-agent-with-skills chat "你好" --debug
```

会输出到标准错误：
- 当前工作目录
- `.env` 候选路径与实际命中的路径
- `base_url`、模型名、`skills_dir`
- 每轮请求的 `stop_reason`
- 工具调用与返回长度

或安装后在任意目录（需能加载 `.env` 与 `skills/`）：

```bash
uv run --directory /path/to/simple-agent-with-skills simple-agent-with-skills chat "你好"
```

## 项目结构

```
simple-agent-with-skills/
  pyproject.toml       # uv / 包元数据与脚本入口
  .env.example
  skills/                # Markdown 技能（可选）
  src/simple_agent_with_skills/
    config.py            # 读取环境变量
    skills.py            # 聚合 skills 文本
    tools.py             # 工具定义与实现
    agent.py             # 异步消息 + 工具循环
    cli.py               # Typer 入口
```

## 扩展方式

- **新工具**：在 `TOOL_DEFINITIONS` 增加 `input_schema`，在 `SYNC_HANDLERS` 注册同名函数；复杂逻辑可在 handler 内再 `async` 包装或 `asyncio.to_thread`。
- **新技能**：在 `skills/` 下新增 `.md` 即可；或通过 `SKILLS_DIR` 指向其他目录。
- **多轮对话**：可在 `agent.py` 中把 `messages` 列表暴露为会话状态，CLI 增加 `repl` 子命令按需拼接历史。


