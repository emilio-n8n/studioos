from __future__ import annotations
import json
from abc import ABC, abstractmethod

from openai import AsyncOpenAI

from app.config import settings, OPENCODE_GO_BASE_URL


SYSTEM_PROMPT = """You are the Strategic Planner for StudioOS, an operating system that designs autonomous organizations to complete complex projects.

Analyze the given project description and produce a structured analysis.

Output ONLY valid JSON with this exact structure:
{
  "name": "Short project name derived from the description",
  "summary": "One paragraph summary of what needs to be built",
  "objectives": ["List of 3-8 specific, measurable objectives"],
  "constraints": ["List of constraints (technical, timeline, resource, etc.)"],
  "complexity": "low" | "medium" | "high" | "critical",
  "complexity_rationale": "Brief explanation of why this complexity level was chosen",
  "risks": [
    {"risk": "Description of risk", "severity": "low" | "medium" | "high", "mitigation": "How to mitigate this risk"}
  ],
  "assumptions": ["List of assumptions made during analysis"],
  "estimated_duration": "Duration estimate (e.g. '2-3 months')",
  "suggested_departments": [
    {"name": "Department name", "description": "What this department handles", "priority": 1}
  ]
}"""


class ProjectAnalysis:
    def __init__(self, data: dict):
        self.name = data.get("name", "Unnamed Project")
        self.summary = data.get("summary", "")
        self.objectives = data.get("objectives", [])
        self.constraints = data.get("constraints", [])
        self.complexity = data.get("complexity", "medium")
        self.complexity_rationale = data.get("complexity_rationale", "")
        self.risks = data.get("risks", [])
        self.assumptions = data.get("assumptions", [])
        self.estimated_duration = data.get("estimated_duration", "unknown")
        self.suggested_departments = data.get("suggested_departments", [])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "summary": self.summary,
            "objectives": self.objectives,
            "constraints": self.constraints,
            "complexity": self.complexity,
            "complexity_rationale": self.complexity_rationale,
            "risks": self.risks,
            "assumptions": self.assumptions,
            "estimated_duration": self.estimated_duration,
            "suggested_departments": self.suggested_departments,
        }


class BaseStrategicPlanner(ABC):
    @abstractmethod
    async def analyze(self, description: str, api_key: str | None = None, provider: str = "openai", model: str | None = None) -> ProjectAnalysis:
        ...


class LLMStrategicPlanner(BaseStrategicPlanner):
    async def analyze(self, description: str, api_key: str | None = None, provider: str = "openai", model: str | None = None) -> ProjectAnalysis:
        if provider == "opencode-go":
            base_url = OPENCODE_GO_BASE_URL
            model_name = model or "deepseek-v4-flash"
        else:
            base_url = None
            model_name = model or settings.openai_model

        client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=60.0)
        try:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Project description:\n\n{description}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
        except Exception as e:
            raise RuntimeError(f"LLM API error: {e}") from e

        if not response.choices:
            raise RuntimeError("LLM returned empty response")
        raw = response.choices[0].message.content
        if not raw:
            raise RuntimeError("LLM returned empty response")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"LLM returned invalid JSON: {e}") from e
        return ProjectAnalysis(data)


class RuleBasedStrategicPlanner(BaseStrategicPlanner):
    async def analyze(self, description: str, api_key: str | None = None, provider: str = "openai", model: str | None = None) -> ProjectAnalysis:
        raise NotImplementedError("Rule-based planner not implemented yet")


class DemoStrategicPlanner(BaseStrategicPlanner):
    async def analyze(self, description: str, api_key: str | None = None, provider: str = "openai", model: str | None = None) -> ProjectAnalysis:
        return ProjectAnalysis({
            "name": "SaaS Landing Page — TaskFlow",
            "summary": "A modern, responsive SaaS landing page for TaskFlow, a project management tool. Features hero section, feature highlights, pricing tiers, and contact form.",
            "objectives": [
                "Hero section with animated value proposition",
                "Feature grid highlighting key capabilities",
                "Three-tier pricing table",
                "Responsive contact form with validation",
                "Smooth scroll navigation and animations",
            ],
            "constraints": [
                "Vanilla HTML/CSS/JS — no frameworks",
                "Mobile-first responsive design",
                "Must be self-contained in 3 files",
            ],
            "complexity": "medium",
            "complexity_rationale": "Standard marketing page with modern UI patterns and responsive design",
            "risks": [
                {"risk": "Design may not match brand guidelines", "severity": "low", "mitigation": "Use clean, neutral design that works for any brand"},
                {"risk": "Contact form needs backend endpoint", "severity": "medium", "mitigation": "Implement client-side validation and demo state"},
            ],
            "assumptions": [
                "Modern browser with ES6+ support",
                "Google Fonts CDN is accessible",
            ],
            "estimated_duration": "1-2 weeks",
            "suggested_departments": [
                {"name": "Design", "description": "UI/UX design and visual identity", "priority": 1},
                {"name": "Frontend", "description": "HTML/CSS/JS implementation", "priority": 1},
                {"name": "Content", "description": "Copywriting and SEO optimization", "priority": 2},
                {"name": "QA", "description": "Cross-browser testing and validation", "priority": 3},
                {"name": "Management", "description": "Coordination and stakeholder communication", "priority": 1},
            ],
        })
