"""use_skill 工具行为测试。"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from simple_agent_with_skills.skills import (
    build_skill_index,
    get_skill_by_name,
    load_skills,
)

# ─── build_skill_index ───────────────────────────────────────────────────────


def test_build_skill_index_empty_when_no_skills(tmp_path: Path) -> None:
    assert build_skill_index([]) == ""


def test_build_skill_index_contains_name_and_description(tmp_path: Path) -> None:
    sd = tmp_path / "my-skill"
    sd.mkdir()
    (sd / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: Helps with X\n---\n# body",
        encoding="utf-8",
    )
    skills = load_skills(tmp_path)
    index = build_skill_index(skills)

    assert "my-skill" in index
    assert "Helps with X" in index


def test_build_skill_index_does_not_contain_full_body(tmp_path: Path) -> None:
    sd = tmp_path / "my-skill"
    sd.mkdir()
    (sd / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: desc\n---\n# Very long body content",
        encoding="utf-8",
    )
    skills = load_skills(tmp_path)
    index = build_skill_index(skills)

    assert "Very long body content" not in index


# ─── get_skill_by_name ───────────────────────────────────────────────────────


def test_get_skill_by_name_returns_skill(tmp_path: Path) -> None:
    sd = tmp_path / "tdd"
    sd.mkdir()
    (sd / "SKILL.md").write_text(
        "---\nname: tdd\ndescription: TDD skill\n---\n# TDD body",
        encoding="utf-8",
    )
    skills = load_skills(tmp_path)
    skill = get_skill_by_name(skills, "tdd")

    assert skill is not None
    assert skill.name == "tdd"
    assert "TDD body" in skill.content


def test_get_skill_by_name_returns_none_for_unknown(tmp_path: Path) -> None:
    skills = load_skills(tmp_path / "nonexistent")
    assert get_skill_by_name(skills, "missing") is None


# ─── use_skill 工具（通过 make_use_skill_handler）────────────────────────────


def test_use_skill_returns_skill_content(tmp_path: Path) -> None:
    sd = tmp_path / "tdd"
    sd.mkdir()
    (sd / "SKILL.md").write_text(
        "---\nname: tdd\ndescription: TDD\n---\n# Red-Green-Refactor",
        encoding="utf-8",
    )

    from simple_agent_with_skills.tools.skill_tools import make_use_skill_handler

    handler = make_use_skill_handler(tmp_path)
    result = handler({"name": "tdd", "reason": "implementing new feature"})

    assert "Red-Green-Refactor" in result


def test_use_skill_returns_error_for_unknown(tmp_path: Path) -> None:
    from simple_agent_with_skills.tools.skill_tools import make_use_skill_handler

    handler = make_use_skill_handler(tmp_path)
    result = handler({"name": "no-such-skill", "reason": "test"})

    data = json.loads(result)
    assert "error" in data


def test_use_skill_logs_activation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    sd = tmp_path / "tdd"
    sd.mkdir()
    (sd / "SKILL.md").write_text(
        "---\nname: tdd\ndescription: TDD\n---\n# content",
        encoding="utf-8",
    )

    from simple_agent_with_skills.tools.skill_tools import make_use_skill_handler

    handler = make_use_skill_handler(tmp_path)
    handler({"name": "tdd", "reason": "need TDD for feature"})

    err = capsys.readouterr().err
    assert "tdd" in err
    assert "need TDD for feature" in err
