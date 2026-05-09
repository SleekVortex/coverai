from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

MAIN_MENU_PROFILE = "📄 Профиль"
MAIN_MENU_PLAN = "💰 Баланс"
MAIN_MENU_HISTORY = "🕘 История писем"
MAIN_MENU_SUBSCRIBE = "💳 Пополнить"
MAIN_MENU_HELP = "❓ Помощь"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру главного меню."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=MAIN_MENU_PROFILE),
                KeyboardButton(text=MAIN_MENU_PLAN),
            ],
            [
                KeyboardButton(text=MAIN_MENU_HISTORY),
                KeyboardButton(text=MAIN_MENU_SUBSCRIBE),
            ],
            [KeyboardButton(text=MAIN_MENU_HELP)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Отправьте резюме или ссылку hh.ru",
    )
