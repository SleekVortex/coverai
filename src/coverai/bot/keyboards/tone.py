from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def tone_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру выбора тона."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧑‍💼 Формальный",
                    callback_data="tone:formal",
                ),
                InlineKeyboardButton(
                    text="💪 Уверенный",
                    callback_data="tone:confident",
                ),
            ],
            [InlineKeyboardButton(text="✂️ Краткий", callback_data="tone:concise")],
        ],
    )
