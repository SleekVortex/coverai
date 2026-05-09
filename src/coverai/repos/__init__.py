"""Persistence repositories."""
from coverai.repos.sqlalchemy import (
    CoverLetterSqlAlchemyRepo,
    GenerationRequestSqlAlchemyRepo,
    ResumeProfileSqlAlchemyRepo,
    SubscriptionSqlAlchemyRepo,
    UserSqlAlchemyRepo,
    VacancySqlAlchemyRepo,
)

__all__ = [
    "CoverLetterSqlAlchemyRepo",
    "GenerationRequestSqlAlchemyRepo",
    "ResumeProfileSqlAlchemyRepo",
    "SubscriptionSqlAlchemyRepo",
    "UserSqlAlchemyRepo",
    "VacancySqlAlchemyRepo",
]
