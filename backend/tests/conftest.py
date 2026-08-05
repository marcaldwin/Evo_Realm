from collections.abc import Iterator
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema

from backend.app.db.models import Base, WorldRecord
from backend.app.db.session import engine
from backend.app.services import world_service
from backend.app.dashboard import service as dashboard_service


@pytest.fixture(scope="session")
def test_session_factory() -> Iterator[sessionmaker]:
    schema_name = f"evorealm_test_{uuid4().hex}"
    with engine.begin() as connection:
        connection.execute(CreateSchema(schema_name))

    test_engine = create_engine(
        engine.url,
        pool_pre_ping=True,
        connect_args={
            "options": f"-csearch_path={schema_name},public"
        },
    )
    Base.metadata.create_all(test_engine)
    factory = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )

    yield factory

    test_engine.dispose()
    with engine.begin() as connection:
        connection.execute(DropSchema(schema_name, cascade=True))


@pytest.fixture
def database_world_store(
    monkeypatch: pytest.MonkeyPatch,
    test_session_factory: sessionmaker,
) -> Iterator[None]:
    monkeypatch.setattr(
        world_service,
        "SessionLocal",
        test_session_factory,
    )
    monkeypatch.setattr(
        dashboard_service,
        "SessionLocal",
        test_session_factory,
    )
    with test_session_factory.begin() as session:
        session.execute(delete(WorldRecord))

    yield

    with test_session_factory.begin() as session:
        session.execute(delete(WorldRecord))
