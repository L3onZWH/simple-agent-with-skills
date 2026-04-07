"""工具注册表：统一管理 JSON Schema 声明与执行 handler。"""

from __future__ import annotations

import json
from typing import Any, Callable

ToolHandler = Callable[[dict[str, Any]], str]

# 运行时全局注册表（定义 + handler 分离存储）
_DEFINITIONS: list[dict[str, Any]] = []
_HANDLERS: dict[str, ToolHandler] = {}


def register_tool(
    *,
    name: str,
    description: str,
    input_schema: dict[str, Any],
    handler: ToolHandler,
) -> None:
    """注册一个工具。重复注册会覆盖上一次定义与 handler。"""
    _DEFINITIONS[:] = [d for d in _DEFINITIONS if d["name"] != name]
    _DEFINITIONS.append(
        {
            "name": name,
            "description": description,
            "input_schema": input_schema,
        }
    )
    _HANDLERS[name] = handler


async def run_tool(name: str, arguments: dict[str, Any]) -> str:
    handler = _HANDLERS.get(name)
    if handler is None:
        return json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False)
    try:
        return handler(arguments)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


# 供 agent.py 读取，始终与注册表同步（返回实时视图）
TOOL_DEFINITIONS: list[dict[str, Any]] = _DEFINITIONS
