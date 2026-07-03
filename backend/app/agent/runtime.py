"""
The agent loop — this is what makes the system *agentic* rather than if-else.

Flow per user message:
  1. Ask the LLM (with the tool catalogue) what to do.
  2. If it requests tool calls:
       - read tools  -> execute now, feed results back
       - action tools-> pause and return an approval request (human-in-the-loop)
  3. Loop until the LLM answers with plain text (no more tool calls) or we hit
     the step limit.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.groq_pool import groq_pool
from app.agent.tools import ToolContext, registry
from app.models.agent_action import ActionStatus, AgentAction
from app.models.user import Role, User

MAX_STEPS = 6


def _system_prompt(user: User) -> dict:
    return {
        "role": "system",
        "content": (
            "You are TalentOS, an HR assistant for a company's employees and admins. "
            f"The current date and time is {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC. "
            "Use it to resolve relative times like 'tomorrow' or 'next Monday 3pm'. "
            f"You are talking to {user.full_name or user.email} (role: {user.role.value}). "
            "Use the provided tools to fetch real data — never invent numbers, balances, "
            "or policies. If a tool returns data, answer from it concisely. "
            "When the user asks you to perform an action (apply leave, send email, "
            "approve a request), CALL the appropriate tool directly with your best "
            "understanding of the arguments — do NOT ask for confirmation in text. "
            "The system automatically pauses action tools for human approval, so a "
            "separate confirmation from you is unnecessary. "
            "If you cannot help with the available tools, say so honestly."
        ),
    }


@dataclass
class AgentResult:
    reply: str
    trace: list[dict] = field(default_factory=list)   # tool calls + results, for the Agent Console
    pending_approval: dict | None = None              # set when an action tool needs sign-off


async def run_agent(
    *,
    user: User,
    db: AsyncSession,
    message: str,
    history: list[dict] | None = None,
) -> AgentResult:
    ctx = ToolContext(user=user, db=db)
    is_admin = user.role == Role.admin
    tools = registry.schemas(include_admin=is_admin)

    messages: list[dict] = [_system_prompt(user)]
    if history:
        # Only trust role/content pairs from the client.
        for m in history:
            if m.get("role") in ("user", "assistant") and m.get("content"):
                messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": message})

    trace: list[dict] = []

    for _ in range(MAX_STEPS):
        resp = await groq_pool.chat(messages, tools=tools)
        msg = resp["choices"][0]["message"]
        tool_calls = msg.get("tool_calls")

        # Rebuild a clean assistant message (drop provider-specific extras).
        assistant_msg: dict = {"role": "assistant", "content": msg.get("content") or ""}
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
        messages.append(assistant_msg)

        if not tool_calls:
            return AgentResult(reply=assistant_msg["content"], trace=trace)

        for tc in tool_calls:
            name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}

            tool = registry.get(name)
            if tool is None:
                result: dict = {"error": f"unknown tool '{name}'"}
            elif tool.admin_only and not is_admin:
                result = {"error": "This action requires an admin."}
            elif tool.is_action:
                # Human-in-the-loop: persist a pending action for the Agent Console
                # and stop so a human can approve/reject before it runs.
                summary = tool.summary_for(args)
                action = AgentAction(
                    company_id=user.company_id,
                    user_id=user.id,
                    tool_name=name,
                    summary=summary,
                    args=args,
                    status=ActionStatus.pending,
                )
                db.add(action)
                await db.commit()
                await db.refresh(action)
                return AgentResult(
                    reply=f"I'm ready to: **{summary}**. Approve to proceed.",
                    trace=trace,
                    pending_approval={
                        "action_id": str(action.id),
                        "tool": name,
                        "args": args,
                        "summary": summary,
                    },
                )
            else:
                result = await tool.handler(ctx, **args)

            trace.append({"tool": name, "args": args, "result": result})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result, default=str),
                }
            )

    return AgentResult(
        reply="I couldn't finish that within the step limit — please rephrase.",
        trace=trace,
    )
