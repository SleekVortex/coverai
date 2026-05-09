from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MVP_TABLES = {
    "users",
    "resume_profiles",
    "generation_requests",
    "cover_letters",
    "vacancies",
    "employers",
    "subscriptions",
}


def test_alembic_upgrade_head_creates_mvp_schema(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'coverai.db'}"
    alembic_config = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_config.set_main_option(
        "script_location",
        str(PROJECT_ROOT / "alembic"),
    )
    alembic_config.attributes["database_url"] = database_url

    command.upgrade(alembic_config, "head")

    engine = create_engine(database_url)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    assert tables >= MVP_TABLES
    assert "alembic_version" in tables
    assert "transactions" not in tables
    assert {column["name"] for column in inspector.get_columns("resume_profiles")} >= {
        "title",
        "resume_text",
    }
