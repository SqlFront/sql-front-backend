"""Общие схемы учебных баз, используемые индивидуальными конфигурациями."""

from collections.abc import Sequence


GAME_ANALYSIS_SCHEMA: dict[str, tuple[str, ...]] = {
    "battle": (
        "id", "battle_name", "start_date", "end_date", "location", "result",
        "importance_level",
    ),
    "battle_enemy_unit": ("battle_id", "enemy_unit_id"),
    "enemy_unit": (
        "id", "unit_name", "unit_type", "commander", "location",
        "formation_date", "destruction_date",
    ),
    "equipment": (
        "id", "unit_id", "equipment_type", "item_name", "quantity",
        "last_replenishment",
    ),
    "equipment_assignment": (
        "id", "soldier_id", "equipment_id", "issue_date", "quantity",
    ),
    "medal": ("id", "medal_name", "establishment_date", "award_criteria"),
    "military_service": ("id", "soldier_id", "unit_id", "start_date", "end_date"),
    "military_unit": (
        "id", "unit_name", "unit_type", "location", "formation_date",
        "combat_efficiency",
    ),
    "soldier": (
        "id", "full_name", "birth_year", "gender", "rank", "branch",
        "enlistment_city", "status", "enlistment_date",
    ),
    "soldier_medal": ("soldier_id", "medal_id", "award_date"),
}


def schema_for_tables(table_names: Sequence[str]) -> dict[str, tuple[str, ...]]:
    """Возвращает схему перечисленных таблиц или сообщает об опечатке в конфигурации."""
    schema: dict[str, tuple[str, ...]] = {}
    unknown: list[str] = []

    for raw_name in table_names:
        table_name = str(raw_name).casefold()
        columns = GAME_ANALYSIS_SCHEMA.get(table_name)
        if columns is None:
            unknown.append(str(raw_name))
        else:
            schema[table_name] = columns

    if unknown:
        raise ValueError(
            "В каталоге учебной БД отсутствуют таблицы: " + ", ".join(sorted(unknown))
        )
    return schema
