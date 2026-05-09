from pydantic import BaseModel


class AnalyticsResponse(BaseModel):
    total_generations: int
    succeeded_generations: int
    failed_generations: int
    credits_spent: int
