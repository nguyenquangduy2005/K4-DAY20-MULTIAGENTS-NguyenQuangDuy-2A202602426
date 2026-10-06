"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    return [
    {
        "name": "explorer",
        "description": (
            "Use when you need to inspect files, documentation, logs, "
            "or data and report relevant facts before making changes."
        ),
        "system_prompt": (
            "You are an explorer. Inspect the requested files carefully "
            "and report concrete facts relevant to the task. "
            "Do not modify files."
        ),
    },
    {
        "name": "implementer",
        "description": (
            "Use when the task requires modifying files, implementing code, "
            "processing data, or running tests and scripts."
        ),
        "system_prompt": (
            "You are an implementer. Make only the changes required by "
            "the delegated task. Run tests or scripts when useful and "
            "report what you changed and verified."
        ),
    },
    {
        "name": "reviewer",
        "description": (
            "Use after implementation when the result should be checked "
            "independently against requirements or edge cases."
        ),
        "system_prompt": (
            "You are an independent reviewer. Check the result against "
            "the supplied requirements and relevant edge cases. "
            "Do not modify files. Report any concrete problems."
        ),
    },
]