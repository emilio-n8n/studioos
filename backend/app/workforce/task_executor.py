import json
import re
import logging

from openai import AsyncOpenAI

from app.config import settings, OPENCODE_GO_BASE_URL

logger = logging.getLogger("studioos.task_executor")

TASK_SYSTEM_PROMPT = """You are an AI worker in a department of a larger organization. Your job is to complete a specific task.

Task: {task_title}
Description: {task_description}
Your Role: {role_title}
Department: {department_name}
Project: {project_name}
Project Summary: {project_summary}

Produce output files that fulfill this task. Format:

===FILE:output/{task_id}/report.md===
Your report content in markdown...

===FILE:output/{task_id}/result.json===
{{
  "status": "completed",
  "summary": "..."
}}
"""


def parse_files_from_llm(text: str) -> list[dict]:
    # Format 1: ===FILE:path===\ncontent
    pattern = r'===FILE:([^\n]+)===\n(.*?)(?=\n===FILE:|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    files = [{"path": p.strip(), "content": c.strip()} for p, c in matches]
    if files:
        return files
    # Format 2: Markdown code blocks
    md_pattern = r'```(?:\w+)?\n(.*?)```'
    md_matches = re.findall(md_pattern, text, re.DOTALL)
    for i, content in enumerate(md_matches):
        files.append({"path": f"output/file_{i}.md", "content": content.strip()})
    return files


async def generate_task_output(
    task_title: str,
    task_description: str,
    role_title: str,
    department_name: str,
    project_name: str,
    project_summary: str,
    task_id: int,
    api_key: str,
    provider: str = "openai",
    model: str | None = None,
) -> list[dict]:
    prompt = TASK_SYSTEM_PROMPT.format(
        task_title=task_title,
        task_description=task_description,
        role_title=role_title,
        department_name=department_name,
        project_name=project_name,
        project_summary=project_summary,
        task_id=task_id,
    )

    if provider == "opencode-go":
        base_url = OPENCODE_GO_BASE_URL
        model_name = model or "deepseek-v4-flash"
    else:
        base_url = None
        model_name = model or settings.openai_model

    client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=60.0)
    response = await client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Complete task #{task_id}: {task_title}"},
        ],
        temperature=0.7,
        max_tokens=2048,
    )

    if not response.choices:
        logger.error(f"LLM response has no choices: model={model_name}")
        return [{"path": f"output/{task_id}/report.md", "content": f"# {task_title}\n\n*Fallback: LLM returned empty response.*"}]

    msg = response.choices[0].message
    finish = response.choices[0].finish_reason
    raw = msg.content
    if not raw:
        logger.error(f"LLM returned empty content: model={model_name}, finish_reason={finish}, tool_calls={msg.tool_calls}")
        return [{"path": f"output/{task_id}/report.md", "content": f"# {task_title}\n\n*Fallback: LLM returned empty response.*"}]

    files = parse_files_from_llm(raw)
    if not files:
        files = [{
            "path": f"output/{task_id}/report.md",
            "content": f"# {task_title}\n\n{raw}",
        }]

    return files
