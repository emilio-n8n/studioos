import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.organization import Organization, StrategicDecision
from app.models.department import Department
from app.models.role import Role
from app.models.agent import Agent
from app.models.task import Task
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectListItem, DecisionResponse
from app.org_intelligence.strategic_planner import LLMStrategicPlanner, DemoStrategicPlanner
from app.org_intelligence.organization_architect import design_organization
from app.org_intelligence.recruiter import define_roles
from app.org_intelligence.agent_factory import create_agents, generate_initial_tasks
from app.kernel.event_bus import event_bus, EVENT_PROJECT_CREATED, EVENT_STRATEGY_GENERATED, EVENT_ORG_CREATED, EVENT_AGENT_SPAWNED, EVENT_TASK_ASSIGNED
from app.kernel.memory_system import memory_system
from app.kernel.log_handler import set_project_context

logger = logging.getLogger("studioos.projects")
router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    is_demo = body.openai_api_key.strip().lower() == "demo"
    provider = body.provider or "openai"
    model = body.model or None

    if is_demo:
        planner = DemoStrategicPlanner()
    else:
        planner = LLMStrategicPlanner()
    try:
        analysis = await planner.analyze(body.description, body.openai_api_key, provider=provider, model=model)
    except Exception as e:
        logger.warning(f"Strategic Planner error: {e}")
        raise HTTPException(status_code=400, detail="Analysis failed. Check your API key and try again.")

    project = Project(
        name=body.name or analysis.name,
        description=body.description,
        status="analyzing",
        complexity=analysis.complexity,
        provider=provider,
        model=model,
        openai_api_key=body.openai_api_key,
        analysis=analysis.to_dict(),
    )
    if body.output_path:
        project.output_path = body.output_path
    db.add(project)
    db.flush()
    set_project_context(project.id)
    logger.info(f"Project #{project.id} created — starting organization design")

    org_design = design_organization(analysis)
    org = Organization(
        project_id=project.id,
        name=org_design["name"],
        hierarchy=org_design["hierarchy"],
    )
    db.add(org)
    db.flush()

    logger.info(f"Organization #{org.id} designed — building departments")
    role_defs = define_roles(analysis.suggested_departments)
    departments_map = {}

    for dept_data in analysis.suggested_departments:
        if isinstance(dept_data, dict):
            dept_name = dept_data.get("name", str(dept_data))
            dept_desc = dept_data.get("description", "")
        else:
            dept_name = str(dept_data)
            dept_desc = ""
        dept = Department(organization_id=org.id, name=dept_name, description=dept_desc)
        db.add(dept)
        db.flush()
        departments_map[dept_name] = dept

    logger.info(f"Departments created: {len(departments_map)}")
    agents_data = create_agents(role_defs)
    tasks_data = generate_initial_tasks(agents_data)
    logger.info(f"Roles: {len(role_defs)}, Agents: {len(agents_data)}, Tasks: {len(tasks_data)}")

    role_agent_map = {}
    for ad in agents_data:
        key = (ad["role_title"], ad["department_name"])
        role_agent_map.setdefault(key, []).append(ad)

    for rd in role_defs:
        dept = departments_map.get(rd["department_name"])
        if not dept:
            continue
        role = Role(
            department_id=dept.id,
            title=rd["title"],
            summary=rd.get("summary", ""),
            responsibilities=rd["responsibilities"],
            authority=rd["authority"],
            permissions=rd.get("permissions", []),
            reports_to=rd["reports_to"],
            required_skills=rd["required_skills"],
            metrics=rd.get("metrics", []),
            status="active",
            is_governance=rd.get("is_governance", False),
            level=rd.get("level", 1),
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

    decisions = [
        StrategicDecision(project_id=project.id, category="complexity", title="Complexité estimée",
                          description=analysis.complexity_rationale, impact=analysis.complexity,
                          extra={"value": analysis.complexity}),
        StrategicDecision(project_id=project.id, category="duration", title="Durée estimée",
                          description=f"Projet estimé à {analysis.estimated_duration}",
                          impact=analysis.estimated_duration),
        StrategicDecision(project_id=project.id, category="structure", title="Structure organisationnelle",
                          description=f"Organisation avec {len(departments_map)} départements et {len(role_defs)} rôles",
                          impact="hierarchical"),
    ]
    for risk in analysis.risks:
        decisions.append(StrategicDecision(
            project_id=project.id, category="risk", title=risk.get("risk", "Risque"),
            description=risk.get("mitigation", ""), impact=risk.get("severity", "medium"),
        ))
    for assumption in analysis.assumptions:
        decisions.append(StrategicDecision(
            project_id=project.id, category="assumption", title="Hypothèse retenue",
            description=assumption, impact="accepted",
        ))
    for d in decisions:
        db.add(d)

    project.status = "ready"
    db.commit()
    db.refresh(project)

    memory_system.store(db, project.id, "strategic_analysis", analysis.to_dict(), type="analysis")
    memory_system.log_audit(db, project.id, "project_created", "StrategicPlanner", {"complexity": analysis.complexity})
    memory_system.log_audit(db, project.id, "organization_created", "OrganizationArchitect",
                            {"departments": len(departments_map), "roles": len(role_defs), "agents": len(agents_data)})
    db.commit()

    try:
        await event_bus.emit_to_project(project.id, EVENT_PROJECT_CREATED, {
            "project_id": project.id, "name": project.name, "complexity": analysis.complexity,
        }, db)
        await event_bus.emit_to_project(project.id, EVENT_STRATEGY_GENERATED, {
            "project_id": project.id, "summary": analysis.summary, "complexity": analysis.complexity,
        }, db)
        await event_bus.emit_to_project(project.id, EVENT_ORG_CREATED, {
            "project_id": project.id, "departments": len(departments_map), "roles": len(role_defs),
        }, db)
        agent_count = len(agents_data)
        await event_bus.emit_to_project(project.id, EVENT_AGENT_SPAWNED, {
            "project_id": project.id, "count": agent_count,
        }, db)
        task_count = len(tasks_data)
        await event_bus.emit_to_project(project.id, EVENT_TASK_ASSIGNED, {
            "project_id": project.id, "count": task_count,
        }, db)
    except Exception as e:
        logger.warning(f"Event bus emit failed: {e}")

    return project


@router.get("", response_model=list[ProjectListItem])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/{project_id}/decisions", response_model=list[DecisionResponse])
def list_decisions(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    decisions = db.query(StrategicDecision).filter(
        StrategicDecision.project_id == project_id
    ).order_by(StrategicDecision.created_at.asc()).all()
    return decisions


@router.get("/models/opencode-go")
def list_opencode_go_models():
    from app.config import get_opencode_go_models
    return {"provider": "opencode-go", "models": get_opencode_go_models()}
