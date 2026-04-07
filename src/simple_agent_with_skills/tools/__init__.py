"""工具包：注册表 + 内置工具 + 文件工具。

导入此包即完成所有内置工具的注册，外部代码可直接：

    from simple_agent_with_skills.tools import TOOL_DEFINITIONS, register_tool, run_tool
"""

# 触发内置工具注册（顺序即工具声明顺序）
import simple_agent_with_skills.tools.builtin  # noqa: F401, E402
import simple_agent_with_skills.tools.file_tools  # noqa: F401, E402
from simple_agent_with_skills.tools.registry import (
    TOOL_DEFINITIONS,
    register_tool,
    run_tool,
)

__all__ = ["TOOL_DEFINITIONS", "register_tool", "run_tool"]
