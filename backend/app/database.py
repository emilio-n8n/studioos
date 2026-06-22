from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_schema():
    """Add missing columns to existing tables (SQLite compat)."""
    import sqlalchemy as sa
    inspector = sa.inspect(engine)
    migrations = [
        ("projects", "output_path", "VARCHAR(500)"),
        ("roles", "is_governance", "BOOLEAN DEFAULT 0"),
        ("roles", "level", "INTEGER DEFAULT 1"),
        ("agents", "agent_type", "VARCHAR(50) DEFAULT 'execution'"),
        ("agents", "provider", "VARCHAR(50) DEFAULT 'native'"),
        ("agents", "external_agent_id", "VARCHAR(255)"),
        ("agents", "capabilities", "JSON DEFAULT '[]'"),
        ("departments", "parent_department_id", "INTEGER"),
    ]
    for table, col, col_type in migrations:
        if table in inspector.get_table_names():
            cols = [c["name"] for c in inspector.get_columns(table)]
            if col not in cols:
                with engine.connect() as conn:
                    conn.execute(
                        sa.text(
                            f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"
                        )
                    )
                    conn.commit()


def init_db():
    import app.models.event_log  # noqa: F401
    import app.models.agent_registry  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _migrate_schema()
