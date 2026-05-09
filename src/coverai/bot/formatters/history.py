from coverai.domain.entities import CoverLetter
from coverai.services.history import HistoryResult


def format_history_list(history: HistoryResult) -> str:
    """Форматирует список истории."""
    if not history.letters:
        return (
            "🕘 История писем\n\n"
            "Пока пусто. Отправьте ссылку на вакансию, и первое письмо появится здесь."
        )

    rows = [
        f"{letter.id}. {letter.vacancy_title} — {letter.employer_name}"
        for letter in history.letters
    ]
    return (
        "🕘 История писем\n\n"
        + "\n".join(rows)
        + "\n\nОткройте письмо командой /history <номер>."
    )


def format_history_detail(letter: CoverLetter) -> str:
    """Форматирует письмо из истории."""
    return f"✉️ {letter.vacancy_title} — {letter.employer_name}\n\n{letter.text}"
