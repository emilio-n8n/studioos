from __future__ import annotations

from typing import Any

from app.integration.registry import registry
from app.integration.native_provider import NativeProvider
from app.integration.mock_provider import MockProvider

DEPARTMENT_ROLE_TEMPLATES: dict[str, list[dict]] = {
    "Game Design": [
        {"title": "Game Director", "summary": "Owns creative vision and final design decisions", "responsibilities": ["Define creative vision", "Approve game design decisions"], "authority": ["Final call on design"], "permissions": ["edit:design_doc", "approve:feature", "assign:task"], "reports_to": None, "required_skills": ["Game design", "Leadership"], "metrics": ["team_satisfaction", "vision_alignment"]},
        {"title": "Gameplay Designer", "summary": "Designs and prototypes core game mechanics", "responsibilities": ["Design core mechanics", "Prototype gameplay systems"], "authority": ["Mechanics design"], "permissions": ["edit:mechanics", "view:design_doc"], "reports_to": "Game Director", "required_skills": ["Game design", "Systems thinking"], "metrics": ["mechanic_complexity", "player_engagement"]},
        {"title": "Level Designer", "summary": "Creates levels and balances difficulty curves", "responsibilities": ["Design levels and environments", "Balance difficulty curves"], "authority": ["Level layout decisions"], "permissions": ["edit:levels", "view:mechanics"], "reports_to": "Game Director", "required_skills": ["Level design", "Spatial reasoning"], "metrics": ["level_completion_rate", "player_retention"]},
    ],
    "Engineering": [
        {"title": "Technical Director", "summary": "Owns architecture and technology decisions", "responsibilities": ["Architecture decisions", "Technology stack selection"], "authority": ["Technical architecture"], "permissions": ["approve:architecture", "merge:code", "assign:task"], "reports_to": None, "required_skills": ["Software architecture", "Engineering management"], "metrics": ["code_quality", "sprint_velocity"]},
        {"title": "Engine Programmer", "summary": "Builds core engine features and optimizes performance", "responsibilities": ["Core engine features", "Performance optimization"], "authority": ["Engine implementation"], "permissions": ["edit:engine_code", "view:architecture"], "reports_to": "Technical Director", "required_skills": ["C++", "Game engines"], "metrics": ["render_performance", "memory_usage"]},
        {"title": "Tools Programmer", "summary": "Develops automation tools and pipelines", "responsibilities": ["Build development tools", "Pipeline automation"], "authority": ["Tooling decisions"], "permissions": ["edit:tooling", "deploy:pipeline"], "reports_to": "Technical Director", "required_skills": ["Python", "Tool development"], "metrics": ["pipeline_speed", "tool_adoption"]},
    ],
    "Art": [
        {"title": "Art Director", "summary": "Defines visual style and upholds quality standards", "responsibilities": ["Visual style guide", "Art quality standards"], "authority": ["Visual direction"], "permissions": ["approve:assets", "edit:style_guide", "assign:task"], "reports_to": None, "required_skills": ["Art direction", "Visual design"], "metrics": ["visual_consistency", "team_velocity"]},
        {"title": "3D Artist", "summary": "Creates 3D models, textures, and materials", "responsibilities": ["Create 3D models and assets", "Texture and material creation"], "authority": ["Asset creation"], "permissions": ["edit:3d_assets", "view:style_guide"], "reports_to": "Art Director", "required_skills": ["Blender", "3D modeling"], "metrics": ["asset_quality", "polygon_efficiency"]},
        {"title": "UI/UX Designer", "summary": "Designs interfaces and user experience flows", "responsibilities": ["Design user interfaces", "User experience flows"], "authority": ["UI/UX design"], "permissions": ["edit:ui_designs", "view:style_guide"], "reports_to": "Art Director", "required_skills": ["UI design", "Figma"], "metrics": ["usability_score", "accessibility_compliance"]},
    ],
    "Management": [
        {"title": "CEO", "summary": "Overall project vision and strategic direction", "responsibilities": ["Overall project vision", "Strategic decisions", "Resource allocation"], "authority": ["Final decision on all matters"], "permissions": ["admin:*", "approve:budget", "assign:exec"], "reports_to": None, "required_skills": ["Leadership", "Strategy", "Management"], "metrics": ["project_health", "team_growth"]},
        {"title": "Producer", "summary": "Manages schedule, team coordination, and risks", "responsibilities": ["Schedule management", "Team coordination", "Risk management"], "authority": ["Production priorities"], "permissions": ["edit:schedule", "view:budget", "assign:task"], "reports_to": None, "required_skills": ["Project management", "Communication"], "metrics": ["on_time_delivery", "risk_resolution"]},
    ],
    "Quality Assurance": [
        {"title": "QA Lead", "summary": "Defines test strategy and owns quality process", "responsibilities": ["Test strategy", "QA process definition"], "authority": ["Quality sign-off"], "permissions": ["approve:release", "edit:test_plan", "assign:task"], "reports_to": None, "required_skills": ["Testing", "Quality processes"], "metrics": ["bug_detection_rate", "test_coverage"]},
        {"title": "QA Tester", "summary": "Executes tests and reports bugs", "responsibilities": ["Execute test cases", "Bug reporting and verification"], "authority": ["Bug reporting"], "permissions": ["edit:bug_reports", "view:test_plan"], "reports_to": "QA Lead", "required_skills": ["Testing", "Attention to detail"], "metrics": ["bugs_found", "test_throughput"]},
    ],
    "Marketing": [
        {"title": "Marketing Lead", "summary": "Owns marketing strategy and brand", "responsibilities": ["Marketing strategy", "Brand management"], "authority": ["Marketing decisions"], "permissions": ["edit:marketing_assets", "approve:campaign", "view:analytics"], "reports_to": None, "required_skills": ["Marketing", "Brand strategy"], "metrics": ["campaign_reach", "conversion_rate"]},
    ],
    "DevOps": [
        {"title": "DevOps Engineer", "summary": "Manages infrastructure, CI/CD, and deployments", "responsibilities": ["CI/CD pipeline", "Infrastructure management", "Deployment automation"], "authority": ["Infrastructure decisions"], "permissions": ["deploy:production", "edit:infra_config", "view:logs"], "reports_to": None, "required_skills": ["Docker", "CI/CD", "Cloud"], "metrics": ["uptime", "deploy_frequency"]},
    ],
    "Data": [
        {"title": "Data Engineer", "summary": "Builds data pipelines and manages databases", "responsibilities": ["Data pipelines", "Database management"], "authority": ["Data architecture"], "permissions": ["edit:data_pipelines", "view:analytics"], "reports_to": None, "required_skills": ["SQL", "Data engineering"], "metrics": ["data_quality", "pipeline_latency"]},
        {"title": "Data Scientist", "summary": "Runs analytics and player behavior analysis", "responsibilities": ["Analytics", "Player behavior analysis"], "authority": ["Data insights"], "permissions": ["edit:models", "view:data"], "reports_to": None, "required_skills": ["ML", "Statistics", "Python"], "metrics": ["model_accuracy", "insight_velocity"]},
    ],
    "Content": [
        {"title": "Content Lead", "summary": "Defines content strategy and writing guidelines", "responsibilities": ["Content strategy", "Writing guidelines"], "authority": ["Content decisions"], "permissions": ["approve:content", "edit:style_guide"], "reports_to": None, "required_skills": ["Writing", "Content strategy"], "metrics": ["content_consistency", "output_volume"]},
        {"title": "Writer", "summary": "Writes narrative content, dialog, and lore", "responsibilities": ["Write narrative content", "Dialog and lore"], "authority": ["Narrative writing"], "permissions": ["edit:narrative", "view:content_guide"], "reports_to": "Content Lead", "required_skills": ["Creative writing", "Narrative design"], "metrics": ["word_count", "narrative_quality"]},
    ],
    "Product": [
        {"title": "Product Manager", "summary": "Drives product strategy and feature prioritization", "responsibilities": ["Product strategy", "Feature prioritization", "Stakeholder management"], "authority": ["Product roadmap"], "permissions": ["edit:roadmap", "approve:feature", "view:analytics"], "reports_to": None, "required_skills": ["Product management", "Strategy"], "metrics": ["feature_adoption", "stakeholder_satisfaction"]},
    ],
}


def get_department_name_key(raw_name: str) -> str | None:
    normalized = raw_name.lower().strip()
    for key in DEPARTMENT_ROLE_TEMPLATES:
        if key.lower() in normalized or normalized in key.lower():
            return key
    return None


GOVERNANCE_TITLES = {
    "CEO": 4, "Director": 3, "Lead": 2, "Manager": 2,
    "Supervisor": 2, "Reviewer": 2, "Planner": 3, "Architect": 3,
}


def infer_role_level(title: str) -> int:
    for keyword, level in GOVERNANCE_TITLES.items():
        if keyword.lower() in title.lower():
            return level
    return 1


def infer_is_governance(title: str) -> bool:
    gov_keywords = [
        "CEO", "Director", "Lead", "Manager", "Supervisor",
        "Reviewer", "Planner", "Architect", "Producer",
    ]
    return any(k.lower() in title.lower() for k in gov_keywords)


def hire_agents_by_capability(
    db: Any,
    required_skills: list[str],
    count: int = 1,
) -> list[dict[str, Any]]:
    from app.database import SessionLocal
    if db is None:
        db = SessionLocal()

    try:
        entries = registry.search_by_capability(
            db, required_skills, min_quality=1
        )
        selected = entries[:count] if entries else []
        results = []
        for entry in selected:
            results.append({
                "name": entry.name,
                "provider": entry.provider,
                "external_id": entry.external_id,
                "capabilities": entry.capabilities or [],
                "cost": entry.cost,
                "speed": entry.speed,
                "quality": entry.quality,
                "registry_id": entry.id,
            })
        return results
    finally:
        if db:
            db.close()


def define_roles(departments: list[dict]) -> list[dict]:
    all_roles = []
    for dept in departments:
        dept_name = dept["name"] if isinstance(dept, dict) else dept
        key = get_department_name_key(dept_name)
        if key:
            templates = DEPARTMENT_ROLE_TEMPLATES[key]
        else:
            templates = [
                {"title": f"{dept_name} Lead", "summary": f"Leads {dept_name} efforts and decisions", "responsibilities": [f"Lead {dept_name} efforts"], "authority": [f"{dept_name} decisions"], "permissions": [f"edit:{dept_name.lower()}"], "reports_to": None, "required_skills": [], "metrics": []},
                {"title": f"{dept_name} Specialist", "summary": f"Executes {dept_name} tasks", "responsibilities": [f"Execute {dept_name} tasks"], "authority": [], "permissions": [f"view:{dept_name.lower()}"], "reports_to": f"{dept_name} Lead", "required_skills": [], "metrics": []},
            ]
        for t in templates:
            role = {
                "department_name": dept_name,
                "title": t["title"],
                "summary": t.get("summary", ""),
                "responsibilities": t["responsibilities"],
                "authority": t["authority"],
                "permissions": t.get("permissions", []),
                "reports_to": t["reports_to"],
                "required_skills": t["required_skills"],
                "metrics": t.get("metrics", []),
            }
            role["is_governance"] = infer_is_governance(t["title"])
            role["level"] = infer_role_level(t["title"])
            all_roles.append(role)
    return all_roles
