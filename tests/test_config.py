from pathlib import Path

import pytest

from simple_agent_with_skills.config import load_settings


def test_load_settings_reads_dotenv_from_current_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    monkeypatch.delenv("SKILLS_DIR", raising=False)

    (tmp_path / ".env").write_text(
        "ANTHROPIC_API_KEY=test-key\n"
        "ANTHROPIC_BASE_URL=https://example.com\n"
        "ANTHROPIC_MODEL=test-model\n",
        encoding="utf-8",
    )

    settings = load_settings()

    assert settings.api_key == "test-key"
    assert settings.base_url == "https://example.com"
    assert settings.model == "test-model"
    assert settings.skills_dir == tmp_path / "skills"


def test_load_settings_uses_dotenv_when_environment_variable_is_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")

    (tmp_path / ".env").write_text(
        "ANTHROPIC_API_KEY=test-key\n",
        encoding="utf-8",
    )

    settings = load_settings()

    assert settings.api_key == "test-key"


def test_load_settings_debug_logs_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    env_path = tmp_path / ".env"
    env_path.write_text("ANTHROPIC_API_KEY=test-key\n", encoding="utf-8")

    settings = load_settings(debug=True)

    captured = capsys.readouterr()
    assert settings.api_key == "test-key"
    assert str(tmp_path) in captured.err
    assert str(env_path) in captured.err
