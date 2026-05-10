from coverai.composition.worker_generation import generate_cover_letter_job
from coverai.domain.enums import Tone


async def generate_cover_letter(
    ctx: dict[str, object],
    user_id: int,
    vacancy_url: str,
    tone: str = Tone.FORMAL.value,
    notify_telegram: bool = True,
    charge_credits: bool = False,
    cost_credits: int = 0,
    generation_request_id: int | None = None,
) -> int:
    """Генерирует сопроводительное письмо."""
    return await generate_cover_letter_job(
        ctx=ctx,
        user_id=user_id,
        vacancy_url=vacancy_url,
        tone=tone,
        notify_telegram=notify_telegram,
        charge_credits=charge_credits,
        cost_credits=cost_credits,
        generation_request_id=generation_request_id,
    )
