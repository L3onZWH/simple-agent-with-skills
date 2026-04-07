"""文件工具：read_file、edit_file。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from simple_agent_with_skills.tools.registry import register_tool


def _read_file_handler(args: dict[str, Any]) -> str:
    path = Path(args["path"])
    if not path.exists():
        return json.dumps({"error": f"文件不存在: {path}"}, ensure_ascii=False)
    if not path.is_file():
        return json.dumps({"error": f"路径不是文件: {path}"}, ensure_ascii=False)

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    offset: int = int(args.get("offset") or 0)
    limit: int | None = int(args["limit"]) if args.get("limit") is not None else None

    if offset or limit is not None:
        end = offset + limit if limit is not None else None
        lines = lines[offset:end]
        text = "".join(lines)

    return text


def _edit_file_handler(args: dict[str, Any]) -> str:
    path = Path(args["path"])
    content: str | None = args.get("content")
    old_string: str | None = args.get("old_string")
    new_string: str | None = args.get("new_string")

    # 模式一：全量写入
    if content is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return json.dumps({"ok": True, "path": str(path)}, ensure_ascii=False)

    # 模式二：字符串替换
    if old_string is not None and new_string is not None:
        if not path.exists():
            return json.dumps({"error": f"文件不存在: {path}"}, ensure_ascii=False)
        original = path.read_text(encoding="utf-8")
        if old_string not in original:
            return json.dumps(
                {"error": f"未找到目标字符串: {old_string!r}"}, ensure_ascii=False
            )
        updated = original.replace(old_string, new_string, 1)
        path.write_text(updated, encoding="utf-8")
        return json.dumps({"ok": True, "path": str(path)}, ensure_ascii=False)

    return json.dumps(
        {
            "error": (
                "参数无效：请提供 'content'（全量写入）"
                " 或同时提供 'old_string' 与 'new_string'（字符串替换）"
            )
        },
        ensure_ascii=False,
    )


register_tool(
    name="read_file",
    description=(
        "读取本地文件内容。支持按行偏移（offset）和行数限制（limit）截取片段。"
        "返回文件文本，出错时返回包含 'error' 字段的 JSON。"
    ),
    input_schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件的绝对路径或相对路径"},
            "offset": {
                "type": "integer",
                "description": "从第几行开始读取（0-indexed，默认 0）",
            },
            "limit": {
                "type": "integer",
                "description": "最多读取多少行（默认读取全部）",
            },
        },
        "required": ["path"],
    },
    handler=_read_file_handler,
)

register_tool(
    name="edit_file",
    description=(
        "编辑本地文件。两种模式：\n"
        "1. 全量写入：提供 'content' 覆盖（或新建）文件。\n"
        "2. 字符串替换：提供 'old_string' 和 'new_string'，替换第一处匹配。\n"
        "成功返回 {\"ok\": true}，失败返回包含 'error' 字段的 JSON。"
    ),
    input_schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件的绝对路径或相对路径"},
            "content": {
                "type": "string",
                "description": "【全量写入模式】新的完整文件内容",
            },
            "old_string": {
                "type": "string",
                "description": "【替换模式】要被替换掉的原始字符串",
            },
            "new_string": {
                "type": "string",
                "description": "【替换模式】替换后的新字符串",
            },
        },
        "required": ["path"],
    },
    handler=_edit_file_handler,
)
