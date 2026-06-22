from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel

from app.database import get_db
from app.models.organization import Organization
from app.models.department import Department
from app.models.role import Role
from app.models.agent import Agent
from app.models.task import Task
from app.schemas.organization import OrganizationResponse, DepartmentResponse, RoleResponse

router = APIRouter(prefix="/api/projects/{project_id}/organization", tags=["organization"])


class CreateDepartmentBody(BaseModel):
    name: str
    description: str = ""
    parent_department_id: int | None = None


def _build_org_response(org: Organization) -> OrganizationResponse:
    depts_resp = []
    for dept in org.departments:
        roles_resp = []
        for role in dept.roles:
            roles_resp.append(RoleResponse(
                id=role.id,
                title=role.title,
                summary=role.summary,
                responsibilities=role.responsibilities,
                authority=role.authority,
                permissions=role.permissions,
                reports_to=role.reports_to,
                required_skills=role.required_skills,
                metrics=role.metrics,
                status=role.status,
                is_governance=role.is_governance or False,
                level=role.level or 1,
            ))
        depts_resp.append(DepartmentResponse(
            id=dept.id,
            name=dept.name,
            description=dept.description,
            parent_department_id=dept.parent_department_id,
            roles=roles_resp,
        ))

    return OrganizationResponse(
        id=org.id,
        project_id=org.project_id,
        name=org.name,
        structure_type=org.structure_type,
        hierarchy=org.hierarchy,
        departments=depts_resp,
    )


@router.get("")
def get_organization(project_id: int, db: Session = Depends(get_db)):
    org = db.query(Organization).options(
        joinedload(Organization.departments)
        .joinedload(Department.roles)
        .joinedload(Role.agents)
    ).filter(Organization.project_id == project_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return _build_org_response(org)


@router.get("/tree")
def get_org_tree(project_id: int, db: Session = Depends(get_db)):
    org = db.query(Organization).options(
        joinedload(Organization.departments)
        .joinedload(Department.roles)
        .joinedload(Role.agents)
    ).filter(Organization.project_id == project_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    nodes = []
    edges = []

    for dept in org.departments:
        dept_node = {
            "id": f"dept-{dept.id}",
            "type": "department",
            "position": {"x": 0, "y": 0},
            "data": {
                "label": dept.name,
                "description": dept.description,
                "type": "department",
                "parent_department_id": dept.parent_department_id,
            },
        }
        nodes.append(dept_node)

        if dept.parent_department_id:
            edges.append({
                "id": f"e-dept-{dept.parent_department_id}-dept-{dept.id}",
                "source": f"dept-{dept.parent_department_id}",
                "target": f"dept-{dept.id}",
                "type": "smoothstep",
            })

        for role in dept.roles:
            role_node = {
                "id": f"role-{role.id}",
                "type": "role",
                "position": {"x": 0, "y": 0},
                "data": {
                    "label": role.title,
                    "summary": role.summary,
                    "type": "role",
                    "level": role.level or 1,
                    "is_governance": role.is_governance or False,
                },
            }
            nodes.append(role_node)
            edges.append({
                "id": f"e-dept-{dept.id}-role-{role.id}",
                "source": f"dept-{dept.id}",
                "target": f"role-{role.id}",
            })

            for agent in role.agents:
                task_title = None
                if agent.current_task_id:
                    t = db.query(Task).filter(Task.id == agent.current_task_id).first()
                    task_title = t.title if t else None
                agent_node = {
                    "id": f"agent-{agent.id}",
                    "type": "agent",
                    "position": {"x": 0, "y": 0},
                    "data": {
                        "label": agent.name,
                        "status": agent.status,
                        "type": "agent",
                        "agent_type": agent.agent_type or "execution",
                        "provider": agent.provider or "native",
                        "current_task_id": agent.current_task_id,
                        "current_task": task_title,
                        "is_active": agent.is_active,
                        "last_active_at": str(agent.last_active_at) if agent.last_active_at else None,
                    },
                }
                nodes.append(agent_node)
                edges.append({
                    "id": f"e-role-{role.id}-agent-{agent.id}",
                    "source": f"role-{role.id}",
                    "target": f"agent-{agent.id}",
                })

    return {"nodes": nodes, "edges": edges}


@router.post("/departments", status_code=201)
def create_sub_department(
    project_id: int,
    body: CreateDepartmentBody,
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(
        Organization.project_id == project_id
    ).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if body.parent_department_id:
        parent = db.query(Department).filter(
            Department.id == body.parent_department_id,
            Department.organization_id == org.id,
        ).first()
        if not parent:
            raise HTTPException(
                status_code=404, detail="Parent department not found"
            )

    dept = Department(
        organization_id=org.id,
        parent_department_id=body.parent_department_id,
        name=body.name,
        description=body.description,
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)

    return {
        "id": dept.id,
        "name": dept.name,
        "parent_department_id": dept.parent_department_id,
    }


@router.get("/departments/{department_id}/tree")
def get_department_subtree(
    project_id: int,
    department_id: int,
    db: Session = Depends(get_db),
):
    dept = db.query(Department).options(
        joinedload(Department.roles).joinedload(Role.agents),
        joinedload(Department.children),
    ).filter(
        Department.id == department_id,
        Department.organization.has(project_id=project_id),
    ).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    nodes = []
    edges = []

    def walk(d: Department, parent_id: str | None):
        node_id = f"dept-{d.id}"
        nodes.append({
            "id": node_id,
            "type": "department",
            "position": {"x": 0, "y": 0},
            "data": {"label": d.name, "description": d.description, "type": "department"},
        })
        if parent_id:
            edges.append({"id": f"e-{parent_id}-{node_id}", "source": parent_id, "target": node_id})

        for role in d.roles:
            role_id = f"role-{role.id}"
            nodes.append({
                "id": role_id,
                "type": "role",
                "position": {"x": 0, "y": 0},
                "data": {"label": role.title, "summary": role.summary, "type": "role", "level": role.level or 1, "is_governance": role.is_governance or False},
            })
            edges.append({"id": f"e-{node_id}-{role_id}", "source": node_id, "target": role_id})
            for agent in role.agents:
                agent_id = f"agent-{agent.id}"
                task_title = None
                if agent.current_task_id:
                    t = db.query(Task).filter(Task.id == agent.current_task_id).first()
                    task_title = t.title if t else None
                nodes.append({
                    "id": agent_id,
                    "type": "agent",
                    "position": {"x": 0, "y": 0},
                    "data": {
                        "label": agent.name,
                        "status": agent.status,
                        "type": "agent",
                        "agent_type": agent.agent_type or "execution",
                        "provider": agent.provider or "native",
                        "current_task_id": agent.current_task_id,
                        "current_task": task_title,
                        "is_active": agent.is_active,
                        "last_active_at": str(agent.last_active_at) if agent.last_active_at else None,
                    },
                })
                edges.append({"id": f"e-{role_id}-{agent_id}", "source": role_id, "target": agent_id})

        for child in d.children:
            walk(child, node_id)

    walk(dept, None)
    return {"nodes": nodes, "edges": edges}
