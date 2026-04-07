"""use_skill 工具：agent 自主识别并按需加载完整 skill 内容。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from simple_agent_with_skills.tools.registry import ToolHandler


def make_use_skill_handler(skills_dir: Path, *, debug: bool = False) -> ToolHandler:
    """返回绑定了 skills_dir 的 use_skill handler。

    在每次 run_chat 调用时用当前 settings.skills_dir 创建，避免全局状态污染。
    """
    from simple_agent_with_skills.skills import get_skill_by_name, load_skills

    def _log(msg: str) -> None:
        if debug:
            print(msg, file=sys.stderr)

    def handler(args: dict[str, Any]) -> str:
        name: str = args.get("name", "").strip()
        reason: str = args.get("reason", "").strip()

        _log(f"\n[skill] ✦ 激活技能: {name}")
        if reason:
            _log(f"[skill]   原因: {reason}")

        skills = load_skills(skills_dir)
        skill = get_skill_by_name(skills, name)
        if skill is None:
            available = ", ".join(s.name for s in skills) or "<无>"
            return json.dumps(
                {
                    "error": f"未找到技能 '{name}'。可用技能: {available}",
                },
                ensure_ascii=False,
            )

        _log(f"[skill]   已加载 {len(skill.content)} 字符内容")
        return skill.content

    return handler


USE_SKILL_DEFINITION: dict[str, Any] = {
    "name": "use_skill",
    "description": (
        "加载指定技能的完整内容。"
        "在开始实现/修复/重构等任务前，若可用技能索引中有适用的技能，"
        "必须先调用此工具获取完整指导，再开始执行。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "技能名称，与技能索引中的名称完全一致",
            },
            "reason": {
                "type": "string",
                "description": "一句话说明为什么此任务需要该技能",
            },
        },
        "required": ["name", "reason"],
    },
}
