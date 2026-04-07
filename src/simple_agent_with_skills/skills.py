"""Skill 加载器。

Skill 目录约定
--------------
skills/
  <skill-name>/
    SKILL.md          ← 主文件，YAML frontmatter 含 name / description
    companion.md      ← 可选伴随文件
    ...

SKILL.md 的 frontmatter 格式
------------------------------
---
name: skill-name
description: 一句话说明，告诉 agent 何时使用此 skill
---

# 正文 ...

@companion.md 语法
-------------------
在 SKILL.md 正文中用 `@filename.md` 引用同目录文件，加载时会将被引用文件
的完整内容内联展开，使 system prompt 完全自包含。
若被引用文件不存在，保留原始 `@filename.md` 文本不崩溃。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# 匹配 YAML frontmatter 块（文件开头的 --- ... --- 部分）
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# 匹配 @filename.md 引用（单词边界外只允许空白/标点，避免误匹配 URL）
_REF_RE = re.compile(r"@([\w\-]+\.md)")


@dataclass
class Skill:
    name: str
    description: str
    content: str
    dir: Path = field(repr=False)


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """返回 (frontmatter_dict, remaining_body)。"""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text

    fm: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip()

    body = text[m.end() :]
    return fm, body


def _inline_refs(content: str, skill_dir: Path) -> str:
    """将 @filename.md 替换为对应文件的完整内容；文件不存在时保留原文。"""

    def _replace(m: re.Match[str]) -> str:
        ref_path = skill_dir / m.group(1)
        if not ref_path.is_file():
            return m.group(0)
        ref_text = ref_path.read_text(encoding="utf-8").strip()
        return f"\n\n{ref_text}\n\n"

    return _REF_RE.sub(_replace, content)


def load_skills(skills_dir: Path) -> list[Skill]:
    """扫描 skills_dir 的每个子目录，加载 SKILL.md 并解析 @companion 引用。"""
    if not skills_dir.is_dir():
        return []

    skills: list[Skill] = []
    for sub in sorted(skills_dir.iterdir()):
        if not sub.is_dir():
            continue
        skill_md = sub / "SKILL.md"
        if not skill_md.is_file():
            continue

        raw = skill_md.read_text(encoding="utf-8")
        fm, body = _parse_frontmatter(raw)
        body = _inline_refs(body.strip(), sub)

        skills.append(
            Skill(
                name=fm.get("name", sub.name),
                description=fm.get("description", ""),
                content=body,
                dir=sub,
            )
        )

    return skills


def get_skill_by_name(skills: list[Skill], name: str) -> Skill | None:
    """按名称查找 skill，找不到返回 None。"""
    return next((s for s in skills if s.name == name), None)


def build_skill_index(skills: list[Skill]) -> str:
    """生成技能索引文本（只含名称和描述，不含正文）。

    用于注入 system prompt，让 agent 自主判断是否需要加载某个 skill。
    """
    if not skills:
        return ""

    rows = "\n".join(f"| {s.name} | {s.description} |" for s in skills)
    return (
        "## 可用技能索引\n\n"
        "在开始任务前，先检查下表中的技能是否适用。"
        "若适用，**立即**调用 `use_skill` 工具加载完整内容，再开始执行任务。\n\n"
        "| 技能名称 | 使用场景 |\n"
        "|----------|----------|\n"
        f"{rows}"
    )


def filter_skills(skills: list[Skill], *, names: list[str] | None) -> list[Skill]:
    """按名称筛选。names=None 时返回全部；有未知名称时抛出 ValueError。"""
    if names is None:
        return skills
    index = {s.name: s for s in skills}
    unknown = [n for n in names if n not in index]
    if unknown:
        raise ValueError(f"未找到技能: {', '.join(unknown)}")
    return [index[n] for n in names]


def load_skills_text(skills_dir: Path, *, names: list[str] | None = None) -> str:
    """将 skill 格式化为单段 system prompt 文本。

    names=None 加载全部；指定名称列表时只加载对应 skill。
    """
    all_skills = load_skills(skills_dir)
    active = filter_skills(all_skills, names=names)
    if not active:
        return ""

    parts: list[str] = []
    for s in active:
        header = f"### Skill: {s.name}"
        if s.description:
            header += f"\n> {s.description}"
        parts.append(f"{header}\n\n{s.content}")

    return "## 已加载技能（来自 skills 目录）\n\n" + "\n\n---\n\n".join(parts)
