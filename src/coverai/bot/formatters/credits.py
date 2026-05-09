def format_credit_balance(credits: int) -> str:
    """Форматирует баланс кредитов."""
    return (
        "💰 Баланс\n\n"
        f"Доступно кредитов: {credits}\n"
        "1 успешная генерация списывает 1 кредит.\n\n"
        "Пополнить mock-платежом: /topup 100\n"
        "Активировать промокод: /redeem WELCOME100"
    )
