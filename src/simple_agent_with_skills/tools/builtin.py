"""内置演示工具：echo、add。"""

from __future__ import annotations

import json
from typing import Any

from simple_agent_with_skills.tools.registry import register_tool


def _echo_handler(args: dict[str, Any]) -> str:
    return str(args.get("text", ""))


def _add_handler(args: dict[str, Any]) -> str:
    a = float(args["a"])
    b = float(args["b"])
    return json.dumps({"result": a + b}, ensure_ascii=False)


register_tool(
    name="echo",
    description="原样返回传入的文本，用于演示工具调用。",
    input_schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "要回显的字符串"},
        },
        "required": ["text"],
    },
    handler=_echo_handler,
)

register_tool(
    name="add",
    description="计算两个浮点数之和。",
    input_schema={
        "type": "object",
        "properties": {
            "a": {"type": "number"},
            "b": {"type": "number"},
        },
        "required": ["a", "b"],
    },
    handler=_add_handler,
)
