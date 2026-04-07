"""从环境变量加载配置（API Key、Base URL、模型、技能目录）。"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str | None
    model: str
    skills_dir: Path
    debug: bool = False


def _debug_log(enabled: bool, message: str) -> None:
    if enabled:
        print(f"[simple-agent-with-skills][debug] {message}", file=sys.stderr)


def load_settings(
    *,
    env_file: Path | None = None,
    debug: bool = False,
) -> Settings:
    if env_file is not None:
        candidates = [env_file]
    else:
        project_root = Path(__file__).resolve().parents[2]
        candidates = [Path.cwd() / ".env", project_root / ".env"]

    _debug_log(debug, f"cwd={Path.cwd()}")
    _debug_log(
        debug,
        "env_candidates=" + ", ".join(str(candidate) for candidate in candidates),
    )

    loaded_files: list[Path] = []
    for candidate in candidates:
        if candidate.is_file():
            loaded_files.append(candidate)
            for key, value in dotenv_values(candidate).items():
                if value is None:
                    continue
                current = os.environ.get(key)
                if current is None or not current.strip():
                    os.environ[key] = value

    _debug_log(
        debug,
        "loaded_env_files="
        + (", ".join(str(path) for path in loaded_files) if loaded_files else "<none>"),
    )

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "未设置 ANTHROPIC_API_KEY。请复制 .env.example 为 .env 并填写密钥。"
        )

    raw_base = os.environ.get("ANTHROPIC_BASE_URL", "").strip()
    base_url: str | None = raw_base or None

    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6").strip()

    raw_skills = os.environ.get("SKILLS_DIR", "").strip()
    if raw_skills:
        skills_dir = Path(raw_skills).expanduser().resolve()
    else:
        skills_dir = Path.cwd() / "skills"

    _debug_log(debug, f"skills_dir={skills_dir}")
    _debug_log(debug, f"base_url={base_url or '<default>'}")
    _debug_log(debug, f"model={model}")
    _debug_log(debug, f"api_key_present={bool(api_key)}")

    return Settings(
        api_key=api_key,
        base_url=base_url,
        model=model,
        skills_dir=skills_dir,
        debug=debug,
    )
