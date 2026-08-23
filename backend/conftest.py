import os
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.email import get_email_sender
from app.database import models_registry  # noqa: F401  (registers all feature tables)
from app.database.base import Base
from app.database.session import get_db
from app.dependencies import rate_limits
from app.dependencies.rate_limit import IpRateLimit, UserRateLimit
from app.main import create_app
from features.auth.constants import DEFAULT_ROLES
from features.resumes.constants import ADDITIONAL_TEMPLATES, ATS_SAFE_TEMPLATES, DEFAULT_TEMPLATES

# Rate limiting is real infrastructure (Redis-backed) that these tests don't
# stand up, and its whole point is to reject a high volume of requests from
# the same identity -- exactly what this suite does deliberately (hundreds
# of register/login calls sharing one test-client IP). Override every named
# limiter to a no-op, by identity, the same way get_db/get_email_sender are
# swapped for fakes below.
_RATE_LIMITERS = [
    limiter
    for limiter in vars(rate_limits).values()
    if isinstance(limiter, (IpRateLimit, UserRateLimit))
]

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://career_os:career_os@localhost:5432/career_os_test",
)
_MAINTENANCE_DATABASE_URL = TEST_DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
_TEST_DB_NAME = TEST_DATABASE_URL.rsplit("/", 1)[1]


async def _ensure_test_database_exists() -> None:
    engine = create_async_engine(_MAINTENANCE_DATABASE_URL, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": _TEST_DB_NAME}
        )
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{_TEST_DB_NAME}"'))
    await engine.dispose()


async def _seed_default_roles(conn: AsyncConnection) -> None:
    roles_table = Base.metadata.tables["roles"]
    now = datetime.now(UTC)
    await conn.execute(
        roles_table.insert(),
        [
            {
                "id": uuid.uuid4(),
                "name": name,
                "description": description,
                "created_at": now,
                "updated_at": now,
            }
            for name, description in DEFAULT_ROLES
        ],
    )


async def _seed_default_resume_templates(conn: AsyncConnection) -> None:
    templates_table = Base.metadata.tables["resume_templates"]
    now = datetime.now(UTC)
    await conn.execute(
        templates_table.insert(),
        [
            {
                "id": uuid.uuid4(),
                "slug": slug,
                "name": name,
                "description": description,
                "is_active": True,
                # Mirrors the real 51d20bd33ee5 migration's data update --
                # this test DB is built via create_all, not alembic, so
                # nothing else sets render_engine to 'latex' for ats_safe.
                # Without this, tests would silently exercise ats_safe's
                # unused HTML template instead of the real LaTeX path.
                "render_engine": "latex" if slug == "ats_safe" else "html",
                "created_at": now,
                "updated_at": now,
            }
            for slug, name, description in (
                DEFAULT_TEMPLATES + ADDITIONAL_TEMPLATES + ATS_SAFE_TEMPLATES
            )
        ],
    )


@pytest_asyncio.fixture(scope="session")
async def test_engine():  # type: ignore[no-untyped-def]
    await _ensure_test_database_exists()
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
def test_session_factory(test_engine):  # type: ignore[no-untyped-def]
    return async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def _reset_database(test_engine) -> AsyncGenerator[None]:  # type: ignore[no-untyped-def]
    async with test_engine.begin() as conn:
        table_names = ", ".join(f'"{t.name}"' for t in reversed(Base.metadata.sorted_tables))
        await conn.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))
        await _seed_default_roles(conn)
        await _seed_default_resume_templates(conn)
    yield


@pytest_asyncio.fixture
async def db_session(test_session_factory) -> AsyncGenerator[AsyncSession]:  # type: ignore[no-untyped-def]
    async with test_session_factory() as session:
        yield session
        await session.commit()


@pytest.fixture
def captured_emails() -> list[dict[str, str]]:
    return []


@pytest_asyncio.fixture
async def client(  # type: ignore[no-untyped-def]
    test_session_factory, captured_emails
) -> AsyncGenerator[AsyncClient]:
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    class FakeEmailSender:
        async def send(self, to: str, subject: str, body: str) -> None:
            captured_emails.append({"to": to, "subject": subject, "body": body})

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_email_sender] = lambda: FakeEmailSender()
    for limiter in _RATE_LIMITERS:
        app.dependency_overrides[limiter] = lambda: None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
