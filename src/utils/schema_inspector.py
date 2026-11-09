import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from config import settings

logger = logging.getLogger("schema_inspector")

ANCHOR_POSITIONS: Dict[str, Dict[str, int]] = {
    "soldier": {"x": -300, "y": 200},
    "soldier_medal": {"x": -620, "y": 0},
    "medal": {"x": -620, "y": -300},
    "military_service": {"x": 150, "y": -100},
    "military_unit": {"x": 500, "y": -100},
    "equipment": {"x": 880, "y": 100},
    "equipment_assignment": {"x": 300, "y": 250},
    "battle": {"x": -500, "y": 600},
    "battle_military_unit": {"x": -80, "y": 350},
    "battle_enemy_unit": {"x": -125, "y": 700},
    "enemy_unit": {"x": 400, "y": 650},
}

DEFAULT_TABLE_DESCRIPTIONS: Dict[str, str] = {
    "soldier": "сведения о военнослужащих",
    "soldier_medal": "награждение солдат",
    "medal": "награды",
    "military_service": "служба солдат в подразделениях",
    "military_unit": "военные подразделения",
    "equipment": "военное снаряжение",
    "equipment_assignment": "выдача оборудования солдатам",
    "battle": "бои и сражения",
    "battle_military_unit": "участие подразделений в битвах",
    "battle_enemy_unit": "выдача оборудования солдатам",
    "enemy_unit": "бои и сражения",
}

DEFAULT_COLUMN_DESCRIPTIONS: Dict[str, Dict[str, str]] = {
    "soldier": {
        "id": "уникальный идентификатор",
        "full_name": "полное имя",
        "birth_year": "год рождения",
        "gender": "пол",
        "rank": "воинское звание",
        "branch": "род войск",
        "enlistment_city": "город призыва",
        "enlistment_date": "дата зачисления на службу",
        "status": "текущий статус солдата",
    },
    "soldier_medal": {
        "award_date": "дата награждения",
        "soldier_id": "ссылка на солдата",
        "medal_id": "ссылка на медаль",
    },
    "medal": {
        "id": "уникальный идентификатор",
        "medal_name": "название",
        "establishment_date": "дата учреждения",
        "award_criteria": "критерии награждения",
    },
    "military_service": {
        "id": "уникальный идентификатор",
        "soldier_id": "ссылка на солдата",
        "unit_id": "сылка на подразделение",
        "start_date": "дата начала службы",
        "end_date": "дата конца службы",
    },
    "military_unit": {
        "id": "уникальный идентификатор",
        "unit_name": "название",
        "unit_type": "тип подразделения",
        "location": "местоположение",
        "formation_date": "дата формирования",
        "combat_efficiency": "боеспособность",
    },
    "equipment": {
        "id": "уникальный идентификатор",
        "unit_id": "ссылка на подразделение",
        "equipment_type": "тип оборудования",
        "item_name": "название предмета",
        "quantity": "количество",
        "last_replenishment": "дата последнего пополнения",
    },
    "equipment_assignment": {
        "id": "уникальный идентификатор",
        "soldier_id": "ссылка на солдата",
        "equipment_id": "ссылка на оборудование",
        "issue_date": "дата выдачи",
        "quantity": "количество",
    },
    "battle": {
        "id": "уникальный идентификатор",
        "battle_name": "название битвы",
        "start_date": "дата начала битвы",
        "end_date": "дата окончания битвы",
        "location": "место проведения",
        "result": "итог битвы",
        "importance_level": "уровень важности",
    },
    "battle_military_unit": {
        "battle_id": "ссылка на битву",
        "unit_id": "ссылка на советское подразделение",
    },
    "battle_enemy_unit": {
        "battle_id": "ссылка на битву",
        "enemy_unit_id": "ссылка на вражеское подразделение",
    },
    "enemy_unit": {
        "id": "уникальный идентификатор",
        "unit_name": "название",
        "unit_type": "тип подразделения",
        "commander": "имя коммандира",
        "location": "местоположение",
        "formation_date": "дата формирования",
        "destruction_date": "дата уничтожения",
    },
}

TYPE_MAP: Dict[str, str] = {
    "int8": "bigint",
    "int4": "integer",
    "int2": "smallint",
    "varchar": "varchar",
    "character varying": "varchar",
    "text": "text",
    "date": "date",
    "numeric": "numeric",
    "bool": "boolean",
    "boolean": "boolean",
    "timestamp": "timestamp",
    "timestamptz": "timestamptz",
}

IGNORED_TABLES = {"schema_migrations", "equipment_audit"}


class SchemaInspector:
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or settings.GAME_DATABASE_URL
        self._engine = None
        self._cache: Optional[Dict[str, Any]] = None

    def _get_engine(self):
        if not self._engine:
            self._engine = create_async_engine(self.db_url, pool_pre_ping=True)
        return self._engine

    async def get_schema(self, refresh: bool = False) -> Dict[str, Any]:
        if self._cache is not None and not refresh:
            return self._cache

        engine = self._get_engine()
        async with engine.connect() as conn:
            columns_query = text("""
                SELECT 
                    c.relname AS table_name,
                    a.attname AS column_name,
                    t.typname AS data_type,
                    a.attnum AS ordinal_position,
                    pgd.description AS column_description,
                    ptd.description AS table_description
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                JOIN pg_catalog.pg_attribute a ON a.attrelid = c.oid
                JOIN pg_catalog.pg_type t ON t.oid = a.atttypid
                LEFT JOIN pg_catalog.pg_description pgd ON pgd.objoid = c.oid AND pgd.objsubid = a.attnum
                LEFT JOIN pg_catalog.pg_description ptd ON ptd.objoid = c.oid AND ptd.objsubid = 0
                WHERE n.nspname = 'public'
                  AND c.relkind = 'r'
                  AND a.attnum > 0
                  AND NOT a.attisdropped
                ORDER BY c.relname, a.attnum;
            """)
            col_results = await conn.execute(columns_query)
            col_rows = col_results.fetchall()

            fk_query = text("""
                SELECT
                    conrelid::regclass::text AS source_table,
                    a_src.attname AS source_column,
                    confrelid::regclass::text AS target_table,
                    a_tgt.attname AS target_column
                FROM pg_catalog.pg_constraint c
                JOIN pg_catalog.pg_attribute a_src ON a_src.attrelid = c.conrelid AND a_src.attnum = c.conkey[1]
                JOIN pg_catalog.pg_attribute a_tgt ON a_tgt.attrelid = c.confrelid AND a_tgt.attnum = c.confkey[1]
                WHERE c.contype = 'f' AND c.connamespace = 'public'::regnamespace;
            """)
            fk_results = await conn.execute(fk_query)
            fk_rows = fk_results.fetchall()

        tables_dict: Dict[str, Dict[str, Any]] = {}
        for row in col_rows:
            table_name = row.table_name
            if table_name in IGNORED_TABLES:
                continue

            if table_name not in tables_dict:
                table_desc = (
                    row.table_description
                    or DEFAULT_TABLE_DESCRIPTIONS.get(table_name)
                    or f"таблица {table_name}"
                )
                tables_dict[table_name] = {
                    "label": table_name,
                    "description": table_desc,
                    "columns": [],
                }

            col_name = row.column_name
            col_type = TYPE_MAP.get(row.data_type, row.data_type)
            col_desc = (
                row.column_description
                or DEFAULT_COLUMN_DESCRIPTIONS.get(table_name, {}).get(col_name)
                or ""
            )
            col_entry: Dict[str, Any] = {
                "title": col_name,
                "type": col_type,
            }
            if col_desc:
                col_entry["description"] = col_desc

            tables_dict[table_name]["columns"].append(col_entry)

        # Build nodes
        nodes = []
        unknown_counter = 0
        for table_name, table_info in tables_dict.items():
            if table_name in ANCHOR_POSITIONS:
                position = ANCHOR_POSITIONS[table_name]
            else:
                unknown_counter += 1
                position = {"x": 800 + (unknown_counter % 3) * 300, "y": 300 + (unknown_counter // 3) * 200}

            nodes.append({
                "id": table_name,
                "position": position,
                "type": "databaseSchema",
                "data": table_info,
            })

        # Build edges
        edges = []
        for r in fk_rows:
            src_tbl = r.source_table.replace('"', '').replace('public.', '')
            src_col = r.source_column
            tgt_tbl = r.target_table.replace('"', '').replace('public.', '')
            tgt_col = r.target_column

            if src_tbl in IGNORED_TABLES or tgt_tbl in IGNORED_TABLES:
                continue
            if src_tbl not in tables_dict or tgt_tbl not in tables_dict:
                continue

            edge_id = f"{src_tbl}-{tgt_tbl}_{src_col}_{tgt_col}"
            edges.append({
                "id": edge_id,
                "source": src_tbl,
                "target": tgt_tbl,
                "sourceHandle": f"source:{src_col}",
                "targetHandle": f"target:{tgt_col}",
            })

        result = {
            "nodes": nodes,
            "edges": edges,
        }
        self._cache = result
        return result


schema_inspector = SchemaInspector()
