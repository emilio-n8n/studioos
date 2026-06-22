"""CEO Agent — LLM prompt, tool definitions, and conversation handler."""

import json
import logging
from typing import AsyncGenerator

from openai import AsyncOpenAI
from sqlalchemy.orm import Session

from app.config import settings, OPENCODE_GO_BASE_URL
from app.workforce.ceo_tools import (
    get_project_status,
    get_org_tree,
    list_agents,
    get_agent_detail,
    run_pipeline,
    send_message_to_agent,
    get_recent_events,
    get_dashboard,
)

logger = logging.getLogger("studioos.ceo_agent")

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_project_status",
            "description": "Get the current status of the project (name, description, status, complexity)",
            "parameters": {
                "type": "object",
                "properties": {"project_id": {"type": "integer", "description": "Project ID"}},
                "required": ["project_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_org_tree",
            "description": "Get the full organization tree: departments, roles, and agents",
            "parameters": {
                "type": "object",
                "properties": {"project_id": {"type": "integer"}},
                "required": ["project_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_agents",
            "description": "List all agents with their current status, activity, and current task",
            "parameters": {
                "type": "object",
                "properties": {"project_id": {"type": "integer"}},
                "required": ["project_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_agent_detail",
            "description": "Get detailed information about a specific agent: role, status, current task, capabilities, recent files",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer"},
                    "agent_id": {"type": "integer", "description": "Agent ID"},
                },
                "required": ["project_id", "agent_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_pipeline",
            "description": "Launch the execution pipeline: runs all tasks through the DAG scheduler, generates the website output",
            "parameters": {
                "type": "object",
                "properties": {"project_id": {"type": "integer"}},
                "required": ["project_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_message_to_agent",
            "description": "Send a direct message to a specific agent. The agent will see it in real-time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer"},
                    "agent_id": {"type": "integer"},
                    "message": {"type": "string", "description": "Message content"},
                },
                "required": ["project_id", "agent_id", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_events",
            "description": "Get recent events/activity log for the project",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer"},
                    "limit": {"type": "integer", "description": "Number of events to return (default 20)"},
                },
                "required": ["project_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_dashboard",
            "description": "Get dashboard statistics: task counts, agent counts, department counts",
            "parameters": {
                "type": "object",
                "properties": {"project_id": {"type": "integer"}},
                "required": ["project_id"],
            },
        },
    },
]

CEO_SYSTEM_PROMPT = """You are the CEO of a software development company. You manage the entire organization through this chat interface.

Your role:
- You oversee the full organization: departments, roles, and agents (AI workers)
- You can launch the pipeline to execute all project tasks
- You can check on any agent's status, current task, and recent work
- You can send direct messages to agents
- You have full visibility into the project status and organization structure

Style:
- Be direct, professional, and concise
- Use French (the user speaks French)
- When you execute an action, tell the user what you're doing
- When something completes, summarize the result briefly
- You can show org structure, agent lists, and task statuses in a readable format

Tools available to you:
1. get_project_status — check project state
2. get_org_tree — view the full organization hierarchy
3. list_agents — see all agents and who's active/busy
4. get_agent_detail — dive into a specific agent's work
5. run_pipeline — launch the execution pipeline
6. send_message_to_agent — message an agent directly
7. get_recent_events — see recent activity
8. get_dashboard — get aggregate statistics

IMPORTANT: Always use tools when the user asks for information or action. Don't make up data — use the tools to get real information from the system."""


TOOL_MAP = {
    "get_project_status": get_project_status,
    "get_org_tree": get_org_tree,
    "list_agents": list_agents,
    "get_agent_detail": get_agent_detail,
    "run_pipeline": run_pipeline,
    "send_message_to_agent": send_message_to_agent,
    "get_recent_events": get_recent_events,
    "get_dashboard": get_dashboard,
}


async def chat_stream(
    project_id: int,
    message: str,
    history: list[dict],
    api_key: str,
    provider: str,
    model: str | None,
    db: Session,
) -> AsyncGenerator[str, None]:
    """Stream a chat response with tool calling support."""

    if provider == "opencode-go":
        base_url = OPENCODE_GO_BASE_URL
        model_name = model or "deepseek-v4-flash"
    else:
        base_url = None
        model_name = model or settings.openai_model

    client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=120.0)

    messages = [{"role": "system", "content": CEO_SYSTEM_PROMPT}]
    for h in history[-10:]:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": message})

    max_turns = 5
    for turn in range(max_turns):
        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            temperature=0.7,
            max_tokens=2048,
            stream=True,
        )

        tool_calls_acc: dict[int, dict] = {}
        content_parts: list[str] = []

        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue

            if delta.content:
                content_parts.append(delta.content)
                yield json.dumps({"type": "token", "content": delta.content}) + "\n"

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_acc:
                        tool_calls_acc[idx] = {"id": "", "function": {"name": "", "arguments": ""}}
                    if tc.id:
                        tool_calls_acc[idx]["id"] = tc.id
                    if tc.function and tc.function.name:
                        tool_calls_acc[idx]["function"]["name"] += tc.function.name
                    if tc.function and tc.function.arguments:
                        tool_calls_acc[idx]["function"]["arguments"] += tc.function.arguments

        # If no tool calls, we're done
        if not tool_calls_acc:
            if content_parts:
                messages.append({"role": "assistant", "content": "".join(content_parts)})
            break

        # Process tool calls
        assistant_content = "".join(content_parts) if content_parts else None
        assistant_msg = {"role": "assistant", "content": assistant_content}
        assistant_msg["tool_calls"] = []
        for idx in sorted(tool_calls_acc.keys()):
            tc = tool_calls_acc[idx]
            assistant_msg["tool_calls"].append({
                "id": tc["id"],
                "type": "function",
                "function": {"name": tc["function"]["name"], "arguments": tc["function"]["arguments"]},
            })
        messages.append(assistant_msg)

        for idx in sorted(tool_calls_acc.keys()):
            tc = tool_calls_acc[idx]
            name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"]["arguments"]) if tc["function"]["arguments"] else {}
            except json.JSONDecodeError:
                args = {}
            args["project_id"] = args.get("project_id", project_id)

            yield json.dumps({"type": "tool_start", "tool": name, "args": args}) + "\n"

            try:
                tool_fn = TOOL_MAP.get(name)
                if not tool_fn:
                    result = {"error": f"Unknown tool: {name}"}
                else:
                    if "db" in tool_fn.__code__.co_varnames:
                        result = await tool_fn(project_id=args.get("project_id", project_id), db=db, **{k: v for k, v in args.items() if k != "project_id"})
                    else:
                        result = await tool_fn(**args)
                result_str = json.dumps(result, ensure_ascii=False, default=str)
            except Exception as e:
                result_str = json.dumps({"error": str(e)}, ensure_ascii=False, default=str)
                logger.exception(f"Tool {name} failed")

            yield json.dumps({"type": "tool_result", "tool": name, "result": result_str}) + "\n"
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result_str,
            })

    yield json.dumps({"type": "done"}) + "\n"
