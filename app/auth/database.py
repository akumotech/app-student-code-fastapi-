from sqlmodel import create_engine, SQLModel, Session
from app.config import settings


engine = create_engine(settings.DATABASE_URL, echo=settings.DATABASE_ECHO_SQL)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
