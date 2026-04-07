"""异步 Anthropic Messages 调用与工具循环。"""

from __future__ import annotations

import sys
from typing import Any

from anthropic import AsyncAnthropic

from simple_agent_with_skills.config import Settings
from simple_agent_with_skills.skills import build_skill_index, load_skills
from simple_agent_with_skills.tools import TOOL_DEFINITIONS, register_tool, run_tool
from simple_agent_with_skills.tools.skill_tools import (
    USE_SKILL_DEFINITION,
    make_use_skill_handler,
)


def _debug_log(enabled: bool, message: str) -> None:
    if enabled:
        print(f"[simple-agent-with-skills][debug] {message}", file=sys.stderr)


def _serialize_content(content: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for block in content:
        btype = getattr(block, "type", None)
        if btype == "text":
            out.append({"type": "text", "text": block.text})
        elif btype == "tool_use":
            out.append(
                {
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                }
            )
    return out


def _text_from_content(content: Any) -> str:
    parts: list[str] = []
    for block in content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts)


_BASE_SYSTEM_PROMPT = """\
你是一个自主的 coding agent。

## 核心行为准则

- **直接行动**：收到实现/修复/重构类任务时，先检查技能索引，若有适用技能立即调用 use_skill，
  然后直接用工具动手，不要先问"你想用什么框架"之类的问题。
  有合理默认值就用默认值（pytest、src layout 等），完成后再说明选择原因。
- **工具优先**：需要读写文件时，用 read_file / edit_file 工具直接操作，不要只输出代码块让用户自己复制粘贴。
- **小步推进**：一次只做一件事，完成后简短汇报结果，等待下一步指令。
- **严格遵循已加载技能**：调用 use_skill 获取技能内容后，严格按其流程执行，不得跳步或简化。

## 工具使用约定

- `use_skill`：加载指定技能的完整内容。**任务开始前必须优先调用**（若有适用技能）。
- `read_file`：读取文件内容，可指定 offset/limit 按行截取。
- `edit_file`：写入或修改文件。新建文件用 content 参数；局部修改用 old_string/new_string。
- 路径使用相对路径（相对于当前工作目录）时，需在回复中说明当前工作目录。
"""


def _build_system_prompt(settings: Settings) -> str:
    skills = load_skills(settings.skills_dir)
    index = build_skill_index(skills)
    if not index:
        return _BASE_SYSTEM_PROMPT
    return _BASE_SYSTEM_PROMPT + "\n" + index


def _get_tool_definitions(settings: Settings) -> list[dict[str, Any]]:
    """返回当次对话使用的工具声明（含动态注册的 use_skill）。"""
    # 每次对话重新绑定 use_skill，使其始终指向当前 skills_dir
    register_tool(
        name="use_skill",
        description=USE_SKILL_DEFINITION["description"],
        input_schema=USE_SKILL_DEFINITION["input_schema"],
        handler=make_use_skill_handler(settings.skills_dir),
    )
    return list(TOOL_DEFINITIONS)


async def run_chat(
    settings: Settings,
    user_message: str,
    *,
    max_tokens: int = 4096,
) -> str:
    client_kwargs: dict[str, Any] = {"api_key": settings.api_key}
    if settings.base_url:
        client_kwargs["base_url"] = settings.base_url

    _debug_log(settings.debug, f"client_base_url={settings.base_url or '<default>'}")
    _debug_log(settings.debug, f"request_model={settings.model}")
    _debug_log(settings.debug, f"skills_dir={settings.skills_dir}")

    client = AsyncAnthropic(**client_kwargs)
    system = _build_system_prompt(settings)
    tool_definitions = _get_tool_definitions(settings)

    messages: list[dict[str, Any]] = [
        {"role": "user", "content": user_message},
    ]

    while True:
        _debug_log(settings.debug, f"messages_count={len(messages)}")
        response = await client.messages.create(
            model=settings.model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            tools=tool_definitions,
        )
        _debug_log(settings.debug, f"stop_reason={response.stop_reason}")

        messages.append(
            {"role": "assistant", "content": _serialize_content(response.content)}
        )

        if response.stop_reason != "tool_use":
            return _text_from_content(response.content) or ""

        tool_blocks: list[dict[str, Any]] = []
        for block in response.content:
            if getattr(block, "type", None) != "tool_use":
                continue
            _debug_log(settings.debug, f"tool_use name={block.name} id={block.id}")
            result = await run_tool(block.name, block.input)
            tool_blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                }
            )
            _debug_log(
                settings.debug, f"tool_result name={block.name} length={len(result)}"
            )

        if not tool_blocks:
            return _text_from_content(response.content) or ""

        messages.append({"role": "user", "content": tool_blocks})
