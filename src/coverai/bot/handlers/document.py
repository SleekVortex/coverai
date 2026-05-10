from coverai.bot.formatters.profile import format_profile_saved
from coverai.bot.helpers.users import ensure_user
from coverai.bot.messages import (
    RESUME_FILE_UNREADABLE_TEXT,
    RESUME_TEXT_TOO_SHORT_TEXT,
)
from coverai.bot.protocols import BotUseCases, IncomingMessage
from coverai.services.profile.errors import ResumeTextTooShortError
from coverai.services.resume_files.errors import (
    ResumeTextNotExtractedError,
    UnsupportedResumeFileError,
)


async def handle_document(message: IncomingMessage, use_cases: BotUseCases) -> None:
    """Обрабатывает файл резюме."""
    user = await ensure_user(message, use_cases)
    if user is None or message.document is None:
        return

    try:
        result = await use_cases.save_resume_file(
            user=user,
            file_id=message.document.file_id,
            file_name=message.document.file_name or "resume",
        )
    except (UnsupportedResumeFileError, ResumeTextNotExtractedError):
        await message.answer(RESUME_FILE_UNREADABLE_TEXT)
        return
    except ResumeTextTooShortError:
        await message.answer(RESUME_TEXT_TOO_SHORT_TEXT)
        return

    await message.answer(format_profile_saved(result))
