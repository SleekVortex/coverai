from sqlalchemy import CheckConstraint, UniqueConstraint, create_engine, insert
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from coverai.domain.enums import (
    CreditTransactionType,
    GenerationStatus,
    Plan,
    SubscriptionStatus,
    Tone,
)
from coverai.infra.db.base import Base
from coverai.infra.db.models import Employer, ResumeProfile, User, Vacancy

MVP_TABLES = {
    "users",
    "resume_profiles",
    "generation_requests",
    "cover_letters",
    "vacancies",
    "employers",
    "subscriptions",
    "credit_transactions",
    "payment_intents",
    "subscription_payment_intents",
    "promo_codes",
    "promo_redemptions",
}


def test_enum_values_match_mvp_scope() -> None:
    assert {plan.value for plan in Plan} == {"free", "standard", "pro"}
    assert {tone.value for tone in Tone} == {"formal", "confident", "concise"}
    assert {status.value for status in GenerationStatus} == {
        "pending",
        "succeeded",
        "failed",
    }
    assert {status.value for status in SubscriptionStatus} == {"active", "expired"}
    assert {kind.value for kind in CreditTransactionType} == {
        "welcome_bonus",
        "top_up",
        "promo",
        "spend",
        "adjustment",
        "refund",
    }


def test_sqlalchemy_metadata_contains_mvp_tables_only() -> None:
    assert set(Base.metadata.tables) == MVP_TABLES
    assert "transactions" not in Base.metadata.tables


def test_required_indexes_are_present() -> None:
    assert index_columns("generation_requests")[
        "ix_generation_requests_user_id_status_created_at"
    ] == ("user_id", "status", "created_at")
    assert index_columns("cover_letters")["ix_cover_letters_user_id_created_at"] == (
        "user_id",
        "created_at",
    )
    assert index_columns("subscriptions")[
        "ix_subscriptions_user_id_status_expires_at"
    ] == ("user_id", "status", "expires_at")


def test_required_unique_constraints_are_present() -> None:
    assert unique_columns("users")["uq_users_telegram_id"] == ("telegram_id",)
    assert unique_columns("resume_profiles")["uq_resume_profiles_user_id"] == (
        "user_id",
    )
    assert unique_columns("vacancies")["uq_vacancies_hh_id"] == ("hh_id",)


def test_resume_profile_has_title_column() -> None:
    assert "title" in column_names("resume_profiles")


def test_required_check_constraints_are_present() -> None:
    assert "ck_users_plan" in check_constraint_names("users")
    assert "ck_generation_requests_status" in check_constraint_names(
        "generation_requests",
    )
    assert "ck_generation_requests_tone" in check_constraint_names(
        "generation_requests",
    )
    assert "ck_cover_letters_tone" in check_constraint_names("cover_letters")
    assert "ck_subscriptions_plan" in check_constraint_names("subscriptions")
    assert "ck_subscriptions_status" in check_constraint_names("subscriptions")
    assert "ck_credit_transactions_type" in check_constraint_names(
        "credit_transactions",
    )


def test_users_telegram_id_is_unique() -> None:
    engine = create_schema()
    insert_user(engine, telegram_id=10)

    try_duplicate(
        engine,
        insert(User).values(telegram_id=10, plan=Plan.FREE.value),
    )


def test_resume_profile_is_unique_per_user() -> None:
    engine = create_schema()
    user_id = insert_user(engine, telegram_id=20)

    with engine.begin() as connection:
        connection.execute(
            insert(ResumeProfile).values(user_id=user_id, resume_text="first profile"),
        )

    try_duplicate(
        engine,
        insert(ResumeProfile).values(user_id=user_id, resume_text="second profile"),
    )


def test_vacancy_hh_id_is_unique() -> None:
    engine = create_schema()
    employer_id = insert_employer(engine, hh_id=30)

    with engine.begin() as connection:
        connection.execute(
            insert(Vacancy).values(
                hh_id=100,
                employer_id=employer_id,
                title="Python Developer",
            ),
        )

    try_duplicate(
        engine,
        insert(Vacancy).values(
            hh_id=100,
            employer_id=employer_id,
            title="Backend Developer",
        ),
    )


def index_columns(table_name: str) -> dict[str, tuple[str, ...]]:
    table = Base.metadata.tables[table_name]
    return {
        str(index.name): tuple(column.name for column in index.columns)
        for index in table.indexes
    }


def column_names(table_name: str) -> set[str]:
    return {column.name for column in Base.metadata.tables[table_name].columns}


def unique_columns(table_name: str) -> dict[str, tuple[str, ...]]:
    table = Base.metadata.tables[table_name]
    return {
        str(constraint.name): tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }


def check_constraint_names(table_name: str) -> set[str]:
    table = Base.metadata.tables[table_name]
    return {
        str(constraint.name)
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }


def create_schema() -> Engine:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def insert_user(engine: Engine, telegram_id: int) -> int:
    with engine.begin() as connection:
        result = connection.execute(
            insert(User).values(telegram_id=telegram_id, plan=Plan.FREE.value),
        )

    return int(result.inserted_primary_key[0])


def insert_employer(engine: Engine, hh_id: int) -> int:
    with engine.begin() as connection:
        result = connection.execute(
            insert(Employer).values(hh_id=hh_id, name="Example Inc"),
        )

    return int(result.inserted_primary_key[0])


def try_duplicate(engine: Engine, statement: object) -> None:
    try:
        with engine.begin() as connection:
            connection.execute(statement)
    except IntegrityError:
        return

    raise AssertionError("duplicate insert did not fail")
