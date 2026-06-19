from __future__ import annotations
from sqlalchemy.orm import Session

from app.models.memory import Memory, AuditLog


class MemorySystem:
    def store(self, db: Session, project_id: int, key: str, value: dict, type: str = "general"):
        entry = Memory(project_id=project_id, key=key, value=value, type=type)
        db.add(entry)
        return entry

    def get(self, db: Session, project_id: int, key: str) -> Memory | None:
        return db.query(Memory).filter_by(project_id=project_id, key=key).order_by(Memory.id.desc()).first()

    def list_by_project(self, db: Session, project_id: int, type: str | None = None):
        q = db.query(Memory).filter_by(project_id=project_id)
        if type:
            q = q.filter_by(type=type)
        return q.order_by(Memory.timestamp.desc()).all()

    def log_audit(self, db: Session, project_id: int, action: str, actor: str, details: dict | None = None):
        entry = AuditLog(project_id=project_id, action=action, actor=actor, details=details)
        db.add(entry)
        return entry

    def get_audit_logs(self, db: Session, project_id: int):
        return db.query(AuditLog).filter_by(project_id=project_id).order_by(AuditLog.timestamp.desc()).all()


memory_system = MemorySystem()
