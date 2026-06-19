from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.organization import Organization
from app.models.department import Department
from app.models.role import Role
from app.schemas.organization import OrganizationResponse, DepartmentResponse, RoleResponse

router = APIRouter(prefix="/api/projects/{project_id}/organization", tags=["organization"])


def _build_org_response(org: Organization) -> OrganizationResponse:
    depts_resp = []
    for dept in org.departments:
        roles_resp = []
        for role in dept.roles:
            roles_resp.append(RoleResponse(
                id=role.id,
                title=role.title,
                responsibilities=role.responsibilities,
                authority=role.authority,
                reports_to=role.reports_to,
                required_skills=role.required_skills,
            ))
        depts_resp.append(DepartmentResponse(
            id=dept.id,
            name=dept.name,
            description=dept.description,
            roles=roles_resp,
        ))

    return OrganizationResponse(
        id=org.id,
        project_id=org.project_id,
        name=org.name,
        hierarchy=org.hierarchy,
        departments=depts_resp,
    )


@router.get("")
def get_organization(project_id: int, db: Session = Depends(get_db)):
    org = db.query(Organization).options(
        joinedload(Organization.departments).joinedload(Department.roles).joinedload(Role.agents)
    ).filter(Organization.project_id == project_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return _build_org_response(org)


@router.get("/tree")
def get_org_tree(project_id: int, db: Session = Depends(get_db)):
    org = db.query(Organization).options(
        joinedload(Organization.departments).joinedload(Department.roles).joinedload(Role.agents)
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
            "data": {"label": dept.name, "description": dept.description, "type": "department"},
        }
        nodes.append(dept_node)

        for role in dept.roles:
            role_node = {
                "id": f"role-{role.id}",
                "type": "role",
                "position": {"x": 0, "y": 0},
                "data": {"label": role.title, "description": role.responsibilities, "type": "role"},
            }
            nodes.append(role_node)
            edges.append({
                "id": f"e-dept-{dept.id}-role-{role.id}",
                "source": f"dept-{dept.id}",
                "target": f"role-{role.id}",
            })

            for agent in role.agents:
                agent_node = {
                    "id": f"agent-{agent.id}",
                    "type": "agent",
                    "position": {"x": 0, "y": 0},
                    "data": {"label": agent.name, "status": agent.status, "type": "agent"},
                }
                nodes.append(agent_node)
                edges.append({
                    "id": f"e-role-{role.id}-agent-{agent.id}",
                    "source": f"role-{role.id}",
                    "target": f"agent-{agent.id}",
                })

    return {"nodes": nodes, "edges": edges}
