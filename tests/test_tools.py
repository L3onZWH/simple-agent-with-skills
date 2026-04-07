"""工具注册表与文件工具的行为测试。"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from simple_agent_with_skills.tools import TOOL_DEFINITIONS, register_tool, run_tool

# ─── registry ────────────────────────────────────────────────────────────────


def test_register_tool_adds_definition_and_handler() -> None:
    def my_tool(args: dict) -> str:
        return "ok"

    register_tool(
        name="my_tool",
        description="测试工具",
        input_schema={
            "type": "object",
            "properties": {"x": {"type": "string"}},
            "required": ["x"],
        },
        handler=my_tool,
    )

    names = [t["name"] for t in TOOL_DEFINITIONS]
    assert "my_tool" in names

    result = asyncio.run(run_tool("my_tool", {"x": "hello"}))
    assert result == "ok"


def test_run_tool_unknown_name_returns_error_json() -> None:
    result = asyncio.run(run_tool("no_such_tool", {}))
    data = json.loads(result)
    assert "error" in data


# ─── read_file ───────────────────────────────────────────────────────────────


def test_read_file_returns_content(tmp_path: Path) -> None:
    target = tmp_path / "hello.txt"
    target.write_text("hello world", encoding="utf-8")

    result = asyncio.run(run_tool("read_file", {"path": str(target)}))
    assert result == "hello world"


def test_read_file_missing_file_returns_error_json(tmp_path: Path) -> None:
    result = asyncio.run(run_tool("read_file", {"path": str(tmp_path / "nope.txt")}))
    data = json.loads(result)
    assert "error" in data


def test_read_file_with_offset_and_limit(tmp_path: Path) -> None:
    target = tmp_path / "lines.txt"
    target.write_text("\n".join(f"line{i}" for i in range(10)), encoding="utf-8")

    result = asyncio.run(
        run_tool("read_file", {"path": str(target), "offset": 2, "limit": 3})
    )
    lines = result.splitlines()
    assert len(lines) == 3
    assert lines[0].startswith("line2")


# ─── edit_file ───────────────────────────────────────────────────────────────


def test_edit_file_full_write_creates_file(tmp_path: Path) -> None:
    target = tmp_path / "new.txt"

    result = asyncio.run(
        run_tool("edit_file", {"path": str(target), "content": "brand new"})
    )
    data = json.loads(result)
    assert data.get("ok") is True
    assert target.read_text(encoding="utf-8") == "brand new"


def test_edit_file_full_write_overwrites_existing(tmp_path: Path) -> None:
    target = tmp_path / "existing.txt"
    target.write_text("old content", encoding="utf-8")

    asyncio.run(run_tool("edit_file", {"path": str(target), "content": "new content"}))

    assert target.read_text(encoding="utf-8") == "new content"


def test_edit_file_string_replace(tmp_path: Path) -> None:
    target = tmp_path / "code.py"
    target.write_text("x = 1\ny = 2\n", encoding="utf-8")

    result = asyncio.run(
        run_tool(
            "edit_file",
            {"path": str(target), "old_string": "x = 1", "new_string": "x = 99"},
        )
    )
    data = json.loads(result)
    assert data.get("ok") is True
    assert target.read_text(encoding="utf-8") == "x = 99\ny = 2\n"


def test_edit_file_string_replace_not_found_returns_error(tmp_path: Path) -> None:
    target = tmp_path / "code.py"
    target.write_text("x = 1\n", encoding="utf-8")

    result = asyncio.run(
        run_tool(
            "edit_file",
            {"path": str(target), "old_string": "z = 9", "new_string": "z = 0"},
        )
    )
    data = json.loads(result)
    assert "error" in data
    assert target.read_text(encoding="utf-8") == "x = 1\n"


def test_edit_file_missing_args_returns_error(tmp_path: Path) -> None:
    result = asyncio.run(run_tool("edit_file", {"path": str(tmp_path / "f.txt")}))
    data = json.loads(result)
    assert "error" in data
