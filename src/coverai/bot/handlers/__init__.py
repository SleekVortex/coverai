from coverai.bot.formatters.credits import format_credit_balance
from coverai.bot.formatters.history import format_history_detail, format_history_list
from coverai.bot.formatters.plan import (
    format_legacy_plan_usage,
    format_plan_usage,
    period_label,
    plan_label,
)
from coverai.bot.formatters.profile import format_profile, format_profile_saved
from coverai.bot.handlers.billing import (
    handle_redeem_command,
    handle_subscribe_command,
    handle_topup_command,
)
from coverai.bot.handlers.document import handle_document
from coverai.bot.handlers.generation import handle_vacancy_url
from coverai.bot.handlers.history import handle_history_command
from coverai.bot.handlers.plan import handle_plan_command
from coverai.bot.handlers.profile import handle_profile_command
from coverai.bot.handlers.start import handle_help_command, handle_start
from coverai.bot.handlers.text import (
    handle_main_menu_text,
    handle_text_message,
    save_resume_from_text,
)
from coverai.bot.handlers.tone_callback import handle_tone_callback
from coverai.bot.helpers.ids import required_id
from coverai.bot.helpers.users import ensure_user
from coverai.bot.keyboards.main_menu import (
    MAIN_MENU_HELP,
    MAIN_MENU_HISTORY,
    MAIN_MENU_PLAN,
    MAIN_MENU_PROFILE,
    MAIN_MENU_SUBSCRIBE,
    main_menu_keyboard,
)
from coverai.bot.keyboards.tone import tone_keyboard
from coverai.bot.messages import (
    CREDITS_EXCEEDED_TEXT,
    GENERATION_ACCEPTED_TEXT,
    HELP_TEXT,
    HISTORY_LETTER_NOT_FOUND_TEXT,
    HISTORY_PAYWALL_TEXT,
    MULTIPLE_VACANCY_URLS_TEXT,
    PROFILE_MISSING_TEXT,
    PROFILE_REQUIRED_TEXT,
    RESUME_FILE_UNREADABLE_TEXT,
    RESUME_TEXT_TOO_SHORT_TEXT,
    START_TEXT,
    SUBSCRIBE_TEXT,
    TELEGRAM_USER_MISSING_TEXT,
    TONE_SELECT_TEXT,
)
from coverai.bot.parsing.callback import tone_from_callback
from coverai.bot.parsing.history import history_letter_id
from coverai.bot.protocols import (
    BotUseCases,
    IncomingCallback,
    IncomingMessage,
    TelegramDocument,
    TelegramUser,
)
from coverai.bot.router import create_router
from coverai.bot.state.pending_tone_store import PendingToneStore

__all__ = [
    "BotUseCases",
    "CREDITS_EXCEEDED_TEXT",
    "GENERATION_ACCEPTED_TEXT",
    "HELP_TEXT",
    "HISTORY_LETTER_NOT_FOUND_TEXT",
    "HISTORY_PAYWALL_TEXT",
    "IncomingCallback",
    "IncomingMessage",
    "MAIN_MENU_HELP",
    "MAIN_MENU_HISTORY",
    "MAIN_MENU_PLAN",
    "MAIN_MENU_PROFILE",
    "MAIN_MENU_SUBSCRIBE",
    "MULTIPLE_VACANCY_URLS_TEXT",
    "PROFILE_MISSING_TEXT",
    "PROFILE_REQUIRED_TEXT",
    "PendingToneStore",
    "RESUME_FILE_UNREADABLE_TEXT",
    "RESUME_TEXT_TOO_SHORT_TEXT",
    "START_TEXT",
    "SUBSCRIBE_TEXT",
    "TELEGRAM_USER_MISSING_TEXT",
    "TONE_SELECT_TEXT",
    "TelegramDocument",
    "TelegramUser",
    "create_router",
    "ensure_user",
    "format_credit_balance",
    "format_history_detail",
    "format_history_list",
    "format_legacy_plan_usage",
    "format_plan_usage",
    "format_profile",
    "format_profile_saved",
    "handle_document",
    "handle_help_command",
    "handle_history_command",
    "handle_main_menu_text",
    "handle_plan_command",
    "handle_profile_command",
    "handle_redeem_command",
    "handle_start",
    "handle_subscribe_command",
    "handle_text_message",
    "handle_tone_callback",
    "handle_topup_command",
    "handle_vacancy_url",
    "history_letter_id",
    "main_menu_keyboard",
    "period_label",
    "plan_label",
    "required_id",
    "save_resume_from_text",
    "tone_from_callback",
    "tone_keyboard",
]
