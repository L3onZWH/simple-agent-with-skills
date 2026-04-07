"""Skill 加载行为测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from simple_agent_with_skills.skills import (
    Skill,
    filter_skills,
    load_skills,
    load_skills_text,
)

# ─── load_skills ─────────────────────────────────────────────────────────────


def test_load_skills_returns_empty_when_dir_missing(tmp_path: Path) -> None:
    result = load_skills(tmp_path / "nonexistent")
    assert result == []


def test_load_skills_returns_empty_when_dir_has_no_skill_subdirs(
    tmp_path: Path,
) -> None:
    (tmp_path / "random.md").write_text("# hi", encoding="utf-8")
    result = load_skills(tmp_path)
    assert result == []


def test_load_skills_parses_name_and_description_from_frontmatter(
    tmp_path: Path,
) -> None:
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: Does something useful\n---\n\n# Body\n\nContent here.",
        encoding="utf-8",
    )

    skills = load_skills(tmp_path)

    assert len(skills) == 1
    s = skills[0]
    assert s.name == "my-skill"
    assert s.description == "Does something useful"
    assert "# Body" in s.content
    assert "Content here." in s.content


def test_load_skills_strips_frontmatter_from_content(tmp_path: Path) -> None:
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: x\n---\n\n# Real content",
        encoding="utf-8",
    )

    skills = load_skills(tmp_path)

    assert "---" not in skills[0].content
    assert "name: my-skill" not in skills[0].content


def test_load_skills_uses_dirname_when_frontmatter_missing(tmp_path: Path) -> None:
    skill_dir = tmp_path / "fallback-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "# No frontmatter\n\nJust content.", encoding="utf-8"
    )

    skills = load_skills(tmp_path)

    assert skills[0].name == "fallback-skill"
    assert skills[0].description == ""


def test_load_skills_skips_subdir_without_SKILL_md(tmp_path: Path) -> None:
    (tmp_path / "no-skill-file").mkdir()
    result = load_skills(tmp_path)
    assert result == []


# ─── @companion.md 内联 ───────────────────────────────────────────────────────


def test_load_skills_inlines_companion_file_reference(tmp_path: Path) -> None:
    skill_dir = tmp_path / "tdd"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: tdd\ndescription: TDD\n---\n\n# TDD\n\nRead @anti-patterns.md for details.",
        encoding="utf-8",
    )
    (skill_dir / "anti-patterns.md").write_text(
        "# Anti-Patterns\n\nNever test mocks.",
        encoding="utf-8",
    )

    skills = load_skills(tmp_path)

    assert "# Anti-Patterns" in skills[0].content
    assert "Never test mocks." in skills[0].content
    assert "@anti-patterns.md" not in skills[0].content


def test_load_skills_keeps_text_when_companion_file_not_found(tmp_path: Path) -> None:
    skill_dir = tmp_path / "broken"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: broken\ndescription: x\n---\n\nRead @missing.md here.",
        encoding="utf-8",
    )

    skills = load_skills(tmp_path)

    # 找不到 companion 时保留原始引用文本，不崩溃
    assert "@missing.md" in skills[0].content


def test_load_skills_multiple_companions_all_inlined(tmp_path: Path) -> None:
    skill_dir = tmp_path / "multi"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: multi\ndescription: x\n---\n\nSee @a.md and also @b.md.",
        encoding="utf-8",
    )
    (skill_dir / "a.md").write_text("# A content", encoding="utf-8")
    (skill_dir / "b.md").write_text("# B content", encoding="utf-8")

    skills = load_skills(tmp_path)

    assert "# A content" in skills[0].content
    assert "# B content" in skills[0].content


# ─── load_skills_text ────────────────────────────────────────────────────────


def test_load_skills_text_returns_empty_for_no_skills(tmp_path: Path) -> None:
    assert load_skills_text(tmp_path / "missing") == ""


def test_load_skills_text_includes_name_description_and_content(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo\ndescription: A demo skill\n---\n\n# Demo\n\nDo things.",
        encoding="utf-8",
    )

    text = load_skills_text(tmp_path)

    assert "demo" in text
    assert "A demo skill" in text
    assert "Do things." in text


# ─── filter_skills ───────────────────────────────────────────────────────────


def test_filter_skills_returns_all_when_names_is_none(tmp_path: Path) -> None:
    for name in ("alpha", "beta", "gamma"):
        d = tmp_path / name
        d.mkdir()
        (d / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: x\n---\n# {name}", encoding="utf-8"
        )

    skills = load_skills(tmp_path)
    result = filter_skills(skills, names=None)
    assert [s.name for s in result] == ["alpha", "beta", "gamma"]


def test_filter_skills_returns_only_matching_names(tmp_path: Path) -> None:
    for name in ("alpha", "beta", "gamma"):
        d = tmp_path / name
        d.mkdir()
        (d / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: x\n---\n# {name}", encoding="utf-8"
        )

    skills = load_skills(tmp_path)
    result = filter_skills(skills, names=["alpha", "gamma"])
    assert [s.name for s in result] == ["alpha", "gamma"]


def test_filter_skills_unknown_name_raises_value_error(tmp_path: Path) -> None:
    d = tmp_path / "alpha"
    d.mkdir()
    (d / "SKILL.md").write_text(
        "---\nname: alpha\ndescription: x\n---\n# alpha", encoding="utf-8"
    )

    skills = load_skills(tmp_path)
    with pytest.raises(ValueError, match="unknown-skill"):
        filter_skills(skills, names=["unknown-skill"])


def test_load_skills_text_with_names_filter(tmp_path: Path) -> None:
    for name in ("alpha", "beta"):
        d = tmp_path / name
        d.mkdir()
        (d / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: desc-{name}\n---\n# {name} content",
            encoding="utf-8",
        )

    text = load_skills_text(tmp_path, names=["alpha"])
    assert "alpha" in text
    assert "beta" not in text


# ─── real skill end-to-end ────────────────────────────────────────────────────


def test_load_skills_text_includes_real_tdd_skill(tmp_path: Path) -> None:
    """用项目自带的 test-driven-development skill 做端到端验证。"""
    from pathlib import Path as P

    real_skills_dir = P(__file__).parents[1] / "skills"
    if not (real_skills_dir / "test-driven-development" / "SKILL.md").exists():
        pytest.skip("real skills dir not found")

    text = load_skills_text(real_skills_dir)

    assert "test-driven-development" in text
    assert "Red-Green-Refactor" in text
    # companion 文件应已内联
    assert "Anti-Pattern" in text
