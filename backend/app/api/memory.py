import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.project import Project
from app.models.memory_node import MemoryNode
from app.schemas.memory import MemoryNodeCreate, MemoryNodeResponse, MemoryNodeUpdate, MemoryGraphResponse

logger = logging.getLogger("studioos.memory")
router = APIRouter(prefix="/api/projects/{project_id}/memory", tags=["memory"])


@router.get("/graph", response_model=MemoryGraphResponse)
def get_memory_graph(project_id: int, db: Session = Depends(get_db)):
    nodes = db.query(MemoryNode).options(
        joinedload(MemoryNode.children)
    ).filter(MemoryNode.project_id == project_id).order_by(MemoryNode.created_at.desc()).all()
    edges = []
    for n in nodes:
        if n.parent_id:
            edges.append({"source": n.parent_id, "target": n.id, "type": "derives_from"})
        if n.superseded_by:
            edges.append({"source": n.id, "target": n.superseded_by, "type": "superseded_by"})
    return MemoryGraphResponse(nodes=nodes, edges=edges)


@router.get("", response_model=list[MemoryNodeResponse])
def list_memory(
    project_id: int,
    key: str | None = None,
    type: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(MemoryNode).filter(MemoryNode.project_id == project_id)
    if key:
        q = q.filter(MemoryNode.key == key)
    if type:
        q = q.filter(MemoryNode.type == type)
    if status:
        q = q.filter(MemoryNode.status == status)
    return q.order_by(MemoryNode.created_at.desc()).all()


@router.get("/{node_id}", response_model=MemoryNodeResponse)
def get_memory_node(project_id: int, node_id: int, db: Session = Depends(get_db)):
    node = db.query(MemoryNode).filter(MemoryNode.id == node_id, MemoryNode.project_id == project_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Memory node not found")
    return node


@router.get("/{node_id}/history", response_model=list[MemoryNodeResponse])
def get_memory_history(project_id: int, node_id: int, db: Session = Depends(get_db)):
    node = db.query(MemoryNode).filter(MemoryNode.id == node_id, MemoryNode.project_id == project_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Memory node not found")
    versions = db.query(MemoryNode).filter(
        MemoryNode.project_id == project_id,
        MemoryNode.key == node.key,
    ).order_by(MemoryNode.version.asc()).all()
    return versions


@router.post("", response_model=MemoryNodeResponse, status_code=201)
def create_memory(project_id: int, body: MemoryNodeCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    latest = db.query(MemoryNode).filter(
        MemoryNode.project_id == project_id,
        MemoryNode.key == body.key,
        MemoryNode.status == "active",
    ).order_by(MemoryNode.version.desc()).first()

    version = (latest.version + 1) if latest else 1

    if latest:
        latest.status = "superseded"
        latest.superseded_by = None

    node = MemoryNode(
        project_id=project_id,
        key=body.key,
        value=body.value,
        type=body.type,
        tags=body.tags,
        parent_id=body.parent_id,
        summary=body.summary,
        created_by=body.created_by,
        status="active",
        version=version,
    )
    if latest:
        node.superseded_by = latest.id

    db.add(node)
    db.commit()
    db.refresh(node)
    logger.info(f"MemoryNode #{node.id} created: {node.key} (v{node.version})")
    return node


@router.patch("/{node_id}", response_model=MemoryNodeResponse)
def update_memory(project_id: int, node_id: int, body: MemoryNodeUpdate, db: Session = Depends(get_db)):
    node = db.query(MemoryNode).filter(MemoryNode.id == node_id, MemoryNode.project_id == project_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Memory node not found")
    if body.status is not None:
        node.status = body.status
    if body.approved_by is not None:
        node.approved_by = body.approved_by
    if body.superseded_by is not None:
        node.superseded_by = body.superseded_by
    db.commit()
    db.refresh(node)
    return node
