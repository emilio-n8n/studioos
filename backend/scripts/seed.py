"""Seed database with a demo project and auto-generate its website."""

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal, init_db
from app.models.project import Project
from app.models.organization import Organization
from app.models.department import Department
from app.models.role import Role
from app.models.agent import Agent
from app.models.task import Task
from app.org_intelligence.strategic_planner import DemoStrategicPlanner
from app.org_intelligence.organization_architect import design_organization
from app.org_intelligence.recruiter import define_roles
from app.org_intelligence.agent_factory import create_agents, generate_initial_tasks
from app.kernel.memory_system import memory_system
from app.workforce.file_manager import file_manager
from app.api.generation import _demo_html, _demo_css, _demo_js


def seed():
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(Project).first()
        if existing:
            print(f"Project #{existing.id} already exists: {existing.name}")
            return

        import asyncio
        planner = DemoStrategicPlanner()
        analysis = asyncio.run(planner.analyze("SaaS landing page for TaskFlow", "demo"))

        project = Project(
            name=analysis.name,
            description="A modern SaaS landing page for TaskFlow project management tool.",
            status="ready",
            complexity=analysis.complexity,
            openai_api_key="demo",
            analysis=analysis.to_dict(),
        )
        db.add(project)
        db.flush()

        org_design = design_organization(analysis)
        org = Organization(
            project_id=project.id,
            name=org_design["name"],
            hierarchy=org_design["hierarchy"],
        )
        db.add(org)
        db.flush()

        role_defs = define_roles(analysis.suggested_departments)
        dept_map = {}
        for dd in analysis.suggested_departments:
            name = dd["name"] if isinstance(dd, dict) else str(dd)
            desc = dd.get("description", "") if isinstance(dd, dict) else ""
            dept = Department(organization_id=org.id, name=name, description=desc)
            db.add(dept)
            db.flush()
            dept_map[name] = dept

        agents_data = create_agents(role_defs)
        tasks_data = generate_initial_tasks(agents_data)
        role_agent_map = {}
        for ad in agents_data:
            role_agent_map.setdefault((ad["role_title"], ad["department_name"]), []).append(ad)

        for rd in role_defs:
            dept = dept_map.get(rd["department_name"])
            if not dept:
                continue
            role = Role(
                department_id=dept.id,
                title=rd["title"],
                responsibilities=rd["responsibilities"],
                authority=rd["authority"],
                reports_to=rd["reports_to"],
                required_skills=rd["required_skills"],
            )
            db.add(role)
            db.flush()
            for ad in role_agent_map.get((rd["title"], rd["department_name"]), []):
                agent = Agent(role_id=role.id, name=ad["name"], status=ad["status"])
                db.add(agent)
                db.flush()
                for td in tasks_data:
                    if td["assigned_agent_name"] == ad["name"]:
                        task = Task(
                            project_id=project.id,
                            department_id=dept.id,
                            assigned_agent_id=agent.id,
                            title=td["title"],
                            description=td["description"],
                            priority=td["priority"],
                            status=td["status"],
                            estimated_cost=td["estimated_cost"],
                        )
                        db.add(task)

        db.commit()
        db.refresh(project)
        print(f"✅ Project #{project.id} created: {project.name}")

        files = [
            {"path": "index.html", "content": _demo_html(project)},
            {"path": "css/style.css", "content": _demo_css()},
            {"path": "js/main.js", "content": _demo_js()},
        ]
        file_manager.save_website(project.id, files)
        url = file_manager.get_output_url(project.id)
        print(f"✅ Website generated at {url}")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
