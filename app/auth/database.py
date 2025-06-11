from sqlmodel import create_engine, SQLModel, Session
from app.config import settings

engine = create_engine(settings.DATABASE_URL, echo=settings.DATABASE_ECHO_SQL)

# Remove the create_db_and_tables function or make it optional
def create_db_and_tables():
    """
    DEPRECATED: Use Alembic migrations instead
    Only use this for testing environments
    """
    if settings.ENVIRONMENT == "development":
        SQLModel.metadata.create_all(engine)
    else:
        raise RuntimeError(
            "Auto-creation disabled. Use 'alembic upgrade head' instead."
        )

def get_session():
    with Session(engine) as session:
        yield session