import json
import re

from openai import AsyncOpenAI

from app.config import settings, OPENCODE_GO_BASE_URL


WEBSITE_SYSTEM_PROMPT = """You are a full-stack web development team. Your job is to build a complete, production-quality website based on the project analysis below.

You must generate a complete website with:
- index.html (main HTML page with embedded structure)
- css/style.css (complete styling)
- js/main.js (interactivity, animations, functionality)

Guidelines:
- Use modern HTML5, CSS3, and vanilla JavaScript (no frameworks)
- Make it responsive and visually polished
- Include proper meta tags, semantic HTML
- Use CSS custom properties for theming
- The site should be complete and ready to open in a browser
- Include fonts from Google Fonts via @import in CSS
- Use smooth animations and transitions

Output format:
===FILE:index.html===
<!DOCTYPE html>
...full HTML content...

===FILE:css/style.css===
...full CSS content...

===FILE:js/main.js===
...full JavaScript content...
"""


def parse_files_from_llm(text: str) -> list[dict]:
    files = []

    # Format 1: ===FILE:path===\ncontent
    pattern = r'===FILE:([^\n]+)===\n(.*?)(?=\n===FILE:|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    for path, content in matches:
        files.append({"path": path.strip(), "content": content.strip()})

    if files:
        return files

    # Format 2: Markdown code blocks ```language\ncontent```
    md_pattern = r'```(?:\w+)?\n(.*?)```'
    md_matches = re.findall(md_pattern, text, re.DOTALL)
    names = ["index.html", "style.css", "script.js"]
    for i, content in enumerate(md_matches):
        path = names[i] if i < len(names) else f"file_{i}.html"
        files.append({"path": path, "content": content.strip()})

    if files:
        return files

    # Fallback: wrap entire response as index.html
    files.append({"path": "index.html", "content": text.strip()})
    return files


async def generate_website_files(
    project_name: str,
    project_description: str,
    analysis: dict,
    departments: list[dict],
    roles: list[dict],
    api_key: str,
    provider: str = "openai",
    model: str | None = None,
) -> list[dict]:
    user_prompt = f"""# Project: {project_name}

## Description
{project_description}

## Strategic Analysis
{json.dumps(analysis, indent=2, ensure_ascii=False)}

## Organization Structure
Departments and their roles:
{json.dumps([
    {"department": d.get("name", ""), "roles": [
        {"title": r.get("title", ""), "responsibilities": r.get("responsibilities", [])}
        for r in roles if r.get("department_name") == d.get("name", "")
    ]}
    for d in departments
], indent=2, ensure_ascii=False)}

Generate a complete website for this project."""

    if provider == "opencode-go":
        base_url = OPENCODE_GO_BASE_URL
        model_name = model or "deepseek-v4-flash"
    else:
        base_url = None
        model_name = model or settings.openai_model

    client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=120.0)
    response = await client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": WEBSITE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=4096,
    )

    if not response.choices:
        raise RuntimeError("LLM returned empty response during website generation")
    raw = response.choices[0].message.content
    if not raw:
        raise RuntimeError("LLM returned empty response during website generation")

    files = parse_files_from_llm(raw)
    if not files:
        raise RuntimeError(f"Could not parse any files from LLM output:\n{raw[:500]}")

    return files
