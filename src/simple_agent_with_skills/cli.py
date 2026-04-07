"""CLI：单轮对话入口。"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Optional  # noqa: F401

import typer
from rich.console import Console
from rich.markdown import Markdown

from simple_agent_with_skills.agent import run_chat
from simple_agent_with_skills.config import load_settings

_console = Console()


def _print_reply(text: str) -> None:
    """TTY 时渲染 Markdown；管道/重定向时输出纯文本。"""
    if sys.stdout.isatty():
        _console.print(Markdown(text))
    else:
        print(text)


app = typer.Typer(help="最小 Anthropic Agent：异步、工具调用、技能目录")
skills_app = typer.Typer(help="管理 skills 目录")
app.add_typer(skills_app, name="skills")


@app.command("version")
def version_cmd() -> None:
    """打印包版本。"""
    from simple_agent_with_skills import __version__

    typer.echo(__version__)


@skills_app.command("list")
def skills_list_cmd(
    env_file: Optional[Path] = typer.Option(
        None,
        "--env-file",
        exists=True,
        dir_okay=False,
        readable=True,
        help="指定 .env 文件路径",
    ),
) -> None:
    """列出 skills 目录中所有可用技能（名称 + 描述）。"""
    from simple_agent_with_skills.skills import load_skills

    settings = load_settings(env_file=env_file)
    skills = load_skills(settings.skills_dir)

    if not skills:
        typer.echo(f"skills 目录中暂无技能：{settings.skills_dir}")
        raise typer.Exit(1)

    typer.echo(f"技能目录：{settings.skills_dir}\n")
    for s in skills:
        desc = f"  {s.description}" if s.description else ""
        typer.echo(f"• {s.name}{desc}")


@app.command("chat")
def chat_cmd(
    message: str = typer.Argument(..., help="发送给模型的用户消息"),
    env_file: Optional[Path] = typer.Option(
        None,
        "--env-file",
        exists=True,
        dir_okay=False,
        readable=True,
        help="指定 .env 文件路径（默认从当前目录加载）",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="输出中间调试日志（配置加载路径、请求参数、工具调用）",
    ),
) -> None:
    """发送一条消息并打印模型回复（含多轮工具调用）。

    示例：

    \b
        simple-agent-with-skills chat "请帮我实现 add(a,b) 函数"
        # agent 会自动识别并加载适用的 skill（如 test-driven-development）
    """

    async def _run() -> None:
        settings = load_settings(
            env_file=env_file,
            debug=debug,
        )
        reply = await run_chat(settings, message)
        _print_reply(reply)

    asyncio.run(_run())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
