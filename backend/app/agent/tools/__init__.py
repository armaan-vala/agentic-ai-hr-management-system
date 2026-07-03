"""
Tool registry for the agent.

A Tool is a typed capability the LLM can invoke. Each carries a JSON-schema for its
args and an async handler. `is_action=True` marks side-effecting tools (send email,
approve leave) which require human approval before running — read tools run freely.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@dataclass
class ToolContext:
    """Everything a tool handler needs to act on behalf of the current user."""

    user: User
    db: AsyncSession


# Handler signature: async (ctx, **kwargs) -> dict
Handler = Callable[..., Awaitable[dict]]


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict  # JSON schema for the arguments object
    handler: Handler
    is_action: bool = False  # True → needs human-in-the-loop approval
    # Builds a human-readable one-liner for the approval prompt / Agent Console.
    summarize: Callable[[dict], str] | None = None

    def summary_for(self, args: dict) -> str:
        if self.summarize:
            return self.summarize(args)
        return f"Run {self.name}"

    def openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class ToolRegistry:
    _tools: dict[str, Tool] = field(default_factory=dict)

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def schemas(self) -> list[dict]:
        return [t.openai_schema() for t in self._tools.values()]


registry = ToolRegistry()

# Import tool modules for their side effect of registering. Keep at bottom to
# avoid circular imports.
from app.agent.tools import leave  # noqa: E402,F401
