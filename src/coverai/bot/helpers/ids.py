def required_id(entity: object) -> int:
    """Возвращает назначенный id сущности."""
    entity_id = getattr(entity, "id", None)
    if not isinstance(entity_id, int):
        raise ValueError("entity id is not assigned")

    return entity_id
