import asyncio
import json
import os
import re
from datetime import date, datetime
from decimal import Decimal
import unittest
import asyncpg


def get_db_dsn(env_var: str, default_url: str) -> str:
    url = os.getenv(env_var, default_url)
    return re.sub(r"^postgresql\+[a-zA-Z0-9_]+:", "postgresql:", url)


TARGET_QUERIES = {
    "0.10": """SELECT unit_name FROM military_unit WHERE unit_name NOT LIKE '%стрелков%';""",
    "0.11": """SELECT item_name FROM equipment WHERE item_name LIKE '____';""",
    "0.13": """SELECT mu.unit_name, COUNT(ms.soldier_id)::int AS total_soldiers
FROM military_unit mu
JOIN military_service ms ON mu.id = ms.unit_id
GROUP BY mu.unit_name
ORDER BY mu.unit_name;""",
    "0.25": """SELECT mu.unit_name,
       MIN(EXTRACT(YEAR FROM ms.start_date) - s.birth_year)::float AS min,
       MAX(EXTRACT(YEAR FROM ms.start_date) - s.birth_year)::float AS max
FROM military_unit mu
JOIN military_service ms ON mu.id = ms.unit_id
JOIN soldier s ON ms.soldier_id = s.id
GROUP BY mu.unit_name
ORDER BY mu.unit_name;""",
    "1.01": """SELECT mu.id AS unit_id, SUM(e.quantity)::int AS total_ammo
FROM military_unit mu
JOIN equipment e ON mu.id = e.unit_id
WHERE mu.location = 'Сталинград' AND e.equipment_type = 'боеприпасы'
GROUP BY mu.id
ORDER BY mu.id;""",
    "1.03": """SELECT s.full_name,
       COUNT(DISTINCT b.id) AS battles_participated,
       DENSE_RANK() OVER (ORDER BY COUNT(DISTINCT b.id) DESC, s.full_name) AS hero_rank
FROM soldier s
JOIN military_service ms ON s.id = ms.soldier_id
JOIN battle_military_unit bmu ON ms.unit_id = bmu.unit_id
JOIN battle b ON bmu.battle_id = b.id
WHERE ms.start_date <= b.end_date AND (ms.end_date IS NULL OR ms.end_date >= b.start_date)
GROUP BY s.full_name
ORDER BY hero_rank
LIMIT 20;""",
    "1.04": """SELECT mu.unit_name,
       mu.combat_efficiency AS initial_efficiency,
       ROUND(100.0 * COUNT(CASE WHEN s.status IN ('убит', 'пропал без вести') THEN 1 END) / COUNT(s.id), 2)::float AS loss_percentage,
       ROUND(mu.combat_efficiency * (1.0 - 1.0 * COUNT(CASE WHEN s.status IN ('убит', 'пропал без вести') THEN 1 END) / COUNT(s.id)), 2)::float AS adjusted_efficiency
FROM military_unit mu
JOIN military_service ms ON ms.unit_id = mu.id
JOIN soldier s ON s.id = ms.soldier_id
GROUP BY mu.id, mu.unit_name, mu.combat_efficiency
ORDER BY mu.combat_efficiency DESC, mu.unit_name;""",
    "1.09": """WITH stalingrad_artillery AS (
    SELECT e.equipment_type,
           SUM(e.quantity) AS total_qty
    FROM military_unit mu
    JOIN equipment e ON mu.id = e.unit_id
    WHERE mu.location = 'Сталинград' AND e.equipment_type = 'артиллерия'
    GROUP BY e.equipment_type
),
stalingrad_soldiers AS (
    SELECT COUNT(DISTINCT ms.soldier_id) AS soldiers_count
    FROM military_service ms
    JOIN military_unit mu ON ms.unit_id = mu.id
    JOIN equipment e ON mu.id = e.unit_id
    WHERE mu.location = 'Сталинград' AND e.equipment_type = 'артиллерия'
)
SELECT sa.equipment_type,
       sa.total_qty::int AS total,
       ROUND(sa.total_qty::numeric / NULLIF(ss.soldiers_count, 0), 2)::float AS per_soldier
FROM stalingrad_artillery sa
CROSS JOIN stalingrad_soldiers ss;""",
    "1.13": """SELECT s.full_name, u.unit_name, e.item_name, ea.quantity, ea.issue_date
FROM soldier s
JOIN military_service ms ON s.id = ms.soldier_id
JOIN military_unit u ON ms.unit_id = u.id
JOIN equipment_assignment ea ON s.id = ea.soldier_id
JOIN equipment e ON ea.equipment_id = e.id
ORDER BY s.full_name, ea.issue_date;""",
    "1.17": """SELECT DISTINCT s.full_name
FROM soldier s
JOIN military_service ms ON s.id = ms.soldier_id
WHERE ms.unit_id IN (
    SELECT id FROM military_unit WHERE location = 'Сталинград'
)
ORDER BY s.full_name;""",
    "1.19": """SELECT EXTRACT(YEAR FROM enlistment_date)::int AS year,
       COUNT(*) AS yearly_enlisted,
       SUM(COUNT(*)) OVER (ORDER BY EXTRACT(YEAR FROM enlistment_date))::int AS cumulative_enlisted
FROM soldier
GROUP BY EXTRACT(YEAR FROM enlistment_date)
ORDER BY year;""",
    "1.20": """WITH yearly_wounded AS (
    SELECT EXTRACT(YEAR FROM ms.end_date)::int AS year,
           COUNT(*) AS wounded_count
    FROM soldier s
    JOIN military_service ms ON s.id = ms.soldier_id
    WHERE s.status = 'ранен' AND ms.end_date IS NOT NULL
    GROUP BY EXTRACT(YEAR FROM ms.end_date)
)
SELECT year,
       wounded_count,
       ROUND(AVG(wounded_count) OVER (), 2)::float AS avg_wounded
FROM yearly_wounded
ORDER BY year;""",
    "1.22": """WITH target_battle AS (
    SELECT id FROM battle WHERE battle_name ILIKE '%Курск%'
)
SELECT eu.unit_name
FROM enemy_unit eu
JOIN battle_enemy_unit beu ON eu.id = beu.enemy_unit_id
WHERE beu.battle_id IN (SELECT id FROM target_battle)
ORDER BY eu.unit_name;""",
    "1.23": """WITH stalingrad_soldiers AS (
    SELECT DISTINCT s.id, s.status
    FROM soldier s
    JOIN military_service ms ON s.id = ms.soldier_id
    JOIN battle_military_unit bmu ON ms.unit_id = bmu.unit_id
    JOIN battle b ON bmu.battle_id = b.id
    WHERE b.battle_name = 'Сталинградская битва'
      AND ms.start_date <= b.end_date
      AND (ms.end_date IS NULL OR ms.end_date >= b.start_date)
),
irrecoverable AS (
    SELECT 'Безвозвратные потери' AS loss_category, COUNT(*)::int AS soldiers_count
    FROM stalingrad_soldiers
    WHERE status IN ('убит', 'пропал без вести')
),
sanitary AS (
    SELECT 'Санитарные потери' AS loss_category, COUNT(*)::int AS soldiers_count
    FROM stalingrad_soldiers
    WHERE status = 'ранен'
)
SELECT loss_category, soldiers_count FROM irrecoverable
UNION ALL
SELECT loss_category, soldiers_count FROM sanitary;""",
    "1.24": """SELECT unit_name,
       combat_efficiency,
       RANK() OVER (ORDER BY combat_efficiency DESC) AS eff_rank,
       DENSE_RANK() OVER (ORDER BY combat_efficiency DESC) AS eff_dense_rank
FROM military_unit
WHERE combat_efficiency IS NOT NULL
ORDER BY combat_efficiency DESC, unit_name;""",
    "1.25": """SELECT u.unit_name,
       s.full_name,
       ms.start_date,
       ROW_NUMBER() OVER (PARTITION BY u.id ORDER BY ms.start_date, s.id) AS recruit_order
FROM military_unit u
JOIN military_service ms ON u.id = ms.unit_id
JOIN soldier s ON ms.soldier_id = s.id
ORDER BY u.unit_name, recruit_order;""",
    "1.26": """SELECT u.unit_name,
       e.item_name,
       e.last_replenishment,
       LAG(e.last_replenishment) OVER (PARTITION BY u.id ORDER BY e.last_replenishment, e.item_name) AS prev_replenishment,
       LEAD(e.last_replenishment) OVER (PARTITION BY u.id ORDER BY e.last_replenishment, e.item_name) AS next_replenishment
FROM equipment e
JOIN military_unit u ON e.unit_id = u.id
ORDER BY u.unit_name, e.last_replenishment, e.item_name;""",
    "2.02": """SELECT CASE 
           WHEN b.importance_level = 'стратегическая' THEN 'Стратегические битвы' 
           ELSE 'Локальные операции' 
       END AS battle_group,
       ROUND(AVG(mu.combat_efficiency)::numeric, 2)::float AS avg_efficiency
FROM battle b
JOIN battle_military_unit bmu ON b.id = bmu.battle_id
JOIN military_unit mu ON bmu.unit_id = mu.id
GROUP BY battle_group
ORDER BY battle_group DESC;""",
    "2.05": """SELECT mu.unit_name,
       (MAX(b.end_date) - MIN(b.start_date))::int AS total_duration,
       COUNT(DISTINCT b.id)::int AS battles_count,
       COUNT(DISTINCT s.id) FILTER (WHERE s.status IN ('убит', 'пропал без вести'))::int AS losses,
       ROUND((COUNT(DISTINCT s.id) FILTER (WHERE s.status IN ('убит', 'пропал без вести')))::numeric / NULLIF(COUNT(DISTINCT b.id), 0), 2)::float AS loss_per_battle_ratio,
       PERCENT_RANK() OVER (ORDER BY (MAX(b.end_date) - MIN(b.start_date)) DESC)::float AS survival_percentile
FROM military_unit mu
JOIN battle_military_unit bmu ON mu.id = bmu.unit_id
JOIN battle b ON bmu.battle_id = b.id
LEFT JOIN military_service ms ON mu.id = ms.unit_id
LEFT JOIN soldier s ON ms.soldier_id = s.id
GROUP BY mu.id, mu.unit_name
ORDER BY total_duration DESC, mu.unit_name;""",
    "2.06": """SELECT mu.unit_name,
       COUNT(DISTINCT ms.soldier_id)::int AS soldiers_total,
       COUNT(DISTINCT e.equipment_type)::int AS equipment_types,
       COUNT(DISTINCT bmu.battle_id)::int AS battles_participated,
       COALESCE(STRING_AGG(DISTINCT m.medal_name, ', ' ORDER BY m.medal_name), 'Нет') AS medals_received
FROM military_unit mu
LEFT JOIN military_service ms ON mu.id = ms.unit_id
LEFT JOIN equipment e ON mu.id = e.unit_id
LEFT JOIN battle_military_unit bmu ON mu.id = bmu.unit_id
LEFT JOIN soldier_medal sm ON ms.soldier_id = sm.soldier_id
LEFT JOIN medal m ON sm.medal_id = m.id
GROUP BY mu.id, mu.unit_name
ORDER BY soldiers_total DESC, mu.unit_name;""",
    "2.07": """SELECT e.equipment_type,
       e.item_name,
       mu.unit_name,
       e.quantity,
       CASE
           WHEN STDDEV(e.quantity) OVER (PARTITION BY e.equipment_type) > 0 
                AND e.quantity < AVG(e.quantity) OVER (PARTITION BY e.equipment_type) - 1.5 * STDDEV(e.quantity) OVER (PARTITION BY e.equipment_type) 
           THEN 'Критический дефицит'
           WHEN e.quantity < AVG(e.quantity) OVER (PARTITION BY e.equipment_type) 
           THEN 'Дефицит'
           ELSE 'Норма'
       END AS status
FROM equipment e
LEFT JOIN military_unit mu ON e.unit_id = mu.id
ORDER BY e.equipment_type, e.quantity, e.item_name;""",
    "2.08": """WITH enemy_battles AS (
    SELECT eu.unit_name,
           COUNT(DISTINCT b.id)::int AS victories,
           COUNT(DISTINCT s.id) FILTER (WHERE s.status IN ('убит', 'пропал без вести'))::float AS total_soviet_losses
    FROM enemy_unit eu
    JOIN battle_enemy_unit beu ON eu.id = beu.enemy_unit_id
    JOIN battle b ON beu.battle_id = b.id
    JOIN battle_military_unit bmu ON b.id = bmu.battle_id
    LEFT JOIN military_service ms ON bmu.unit_id = ms.unit_id 
         AND ms.start_date <= b.end_date AND (ms.end_date IS NULL OR ms.end_date >= b.start_date)
    LEFT JOIN soldier s ON ms.soldier_id = s.id
    WHERE b.result ~* '(победа вермахта|потеря города)'
    GROUP BY eu.id, eu.unit_name
)
SELECT unit_name, victories, total_soviet_losses
FROM enemy_battles
ORDER BY victories DESC, total_soviet_losses DESC, unit_name
LIMIT 3;""",
    "2.10": """WITH unit_stats AS (
    SELECT mu.id AS unit_id,
           mu.unit_name,
           COUNT(DISTINCT b.id) FILTER (WHERE b.result ~* '(побед|успеш|освобожд|разгром|взятие|капитуляц)' AND b.result !~* 'вермахт')::int AS victories,
           COUNT(DISTINCT s.id) FILTER (WHERE s.status IN ('убит', 'пропал без вести'))::int AS deaths
    FROM military_unit mu
    LEFT JOIN battle_military_unit bmu ON mu.id = bmu.unit_id
    LEFT JOIN battle b ON bmu.battle_id = b.id
    LEFT JOIN military_service ms ON mu.id = ms.unit_id
    LEFT JOIN soldier s ON ms.soldier_id = s.id
    GROUP BY mu.id, mu.unit_name
),
unit_medals AS (
    SELECT mu.id AS unit_id,
           m.medal_name,
           COUNT(sm.medal_id)::int AS awarded
    FROM military_unit mu
    JOIN military_service ms ON mu.id = ms.unit_id
    JOIN soldier_medal sm ON ms.soldier_id = sm.soldier_id
    JOIN medal m ON sm.medal_id = m.id
    GROUP BY mu.id, m.medal_name
)
SELECT us.unit_name,
       um.medal_name,
       um.awarded,
       us.deaths,
       us.victories,
       ROUND(us.victories::numeric / NULLIF(um.awarded, 0), 2)::float AS victory_per_medal,
       ROUND(us.deaths::numeric / NULLIF(um.awarded, 0), 2)::float AS death_per_medal
FROM unit_medals um
JOIN unit_stats us ON um.unit_id = us.unit_id
ORDER BY CASE WHEN us.victories = 0 THEN 1 ELSE 0 END, victory_per_medal DESC, us.unit_name, um.medal_name;""",
    "2.11": """WITH all_months AS (
    SELECT m AS month_num,
           TRIM(TO_CHAR(TO_DATE(m::text, 'MM'), 'Month')) AS month_name
    FROM generate_series(1, 12) m
),
monthly_battles AS (
    SELECT EXTRACT(MONTH FROM end_date)::int AS month_num,
           COUNT(*) AS total_battles,
           COUNT(*) FILTER (WHERE result ~* '(побед|успеш|освобожд|разгром|взятие|капитуляц)' AND result !~* 'вермахт') AS victories
    FROM battle
    GROUP BY EXTRACT(MONTH FROM end_date)::int
)
SELECT am.month_num,
       am.month_name,
       COALESCE(mb.total_battles, 0)::int AS total_battles,
       COALESCE(ROUND(mb.victories * 100.0 / NULLIF(mb.total_battles, 0), 1)::float, 0.0) AS win_percentage
FROM all_months am
LEFT JOIN monthly_battles mb ON am.month_num = mb.month_num
ORDER BY am.month_num;""",
    "2.12": """WITH battle_units AS (
    SELECT bmu.battle_id,
           ROUND(AVG(mu.combat_efficiency)::numeric, 1)::float AS avg_efficiency
    FROM battle_military_unit bmu
    JOIN military_unit mu ON bmu.unit_id = mu.id
    GROUP BY bmu.battle_id
),
battle_soldiers AS (
    SELECT b.id AS battle_id,
           b.battle_name,
           COUNT(DISTINCT s.id) FILTER (WHERE s.status IN ('убит', 'пропал без вести'))::int AS losses,
           COALESCE(SUM(ea.quantity), 0)::int AS equipment_used
    FROM battle b
    JOIN battle_military_unit bmu ON b.id = bmu.battle_id
    LEFT JOIN military_service ms ON bmu.unit_id = ms.unit_id
         AND ms.start_date <= b.end_date AND (ms.end_date IS NULL OR ms.end_date >= b.start_date)
    LEFT JOIN soldier s ON ms.soldier_id = s.id
    LEFT JOIN equipment_assignment ea ON s.id = ea.soldier_id
    GROUP BY b.id, b.battle_name
),
battle_stats AS (
    SELECT bs.battle_name,
           bs.losses,
           bu.avg_efficiency,
           bs.equipment_used
    FROM battle_soldiers bs
    JOIN battle_units bu ON bs.battle_id = bu.battle_id
)
SELECT battle_name,
       losses,
       avg_efficiency,
       equipment_used,
       DENSE_RANK() OVER (ORDER BY losses DESC)::int AS loss_rank,
       DENSE_RANK() OVER (ORDER BY avg_efficiency DESC)::int AS eff_rank,
       ROUND((losses / NULLIF(avg_efficiency, 0))::numeric, 2)::float AS cost_ratio
FROM battle_stats
ORDER BY cost_ratio DESC, battle_name;""",
}


def serialize_record_val(val):
    if isinstance(val, (date, datetime)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    return val


class TestCurriculumQueries(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        dsn = get_db_dsn("GAME_DATABASE_URL", "postgresql://sql_runner:secret@localhost:5430/game_db")
        try:
            self.conn = await asyncio.wait_for(
                asyncpg.connect(dsn),
                timeout=10.0
            )
        except Exception as e:
            self.skipTest(f"Database at {dsn} is not reachable ({e})")

    async def asyncTearDown(self):
        if hasattr(self, "conn") and self.conn:
            await self.conn.close()

    async def test_all_target_queries_execute_and_serialize(self):
        for task_code, query in TARGET_QUERIES.items():
            with self.subTest(task=task_code):
                stmt = await self.conn.prepare(query)
                columns = [attr.name for attr in stmt.get_attributes()]
                records = await stmt.fetch()

                self.assertTrue(len(columns) > 0, f"{task_code}: columns should not be empty")
                self.assertTrue(len(records) > 0, f"{task_code}: records should return rows")

                data = []
                for r in records:
                    row_vals = [serialize_record_val(r[col]) for col in columns]
                    data.append(row_vals)

                result_json = json.dumps({"columns": columns, "data": data, "row_count": len(data)}, ensure_ascii=False)
                self.assertTrue(len(result_json) > 0)

    async def test_task_0_25_matches_users_db_expected_result(self):
        users_dsn = get_db_dsn("DATABASE_URL", "postgresql://postgres:postgres@localhost:5430/users_db")
        try:
            users_conn = await asyncio.wait_for(asyncpg.connect(users_dsn), timeout=10.0)
        except Exception as e:
            self.skipTest(f"users_db not reachable at {users_dsn} ({e})")

        try:
            row = await users_conn.fetchrow(
                "SELECT correct_query, expected_result FROM tasks WHERE mission_id = 0 AND task_id = 25;"
            )
            self.assertIsNotNone(row, "Task 0.25 should exist in tasks table")
            self.assertIsNotNone(row["correct_query"], "correct_query should not be NULL for task 0.25")
            self.assertIn("ORDER BY mu.unit_name", row["correct_query"])

            expected_payload = json.loads(row["expected_result"]) if isinstance(row["expected_result"], str) else row["expected_result"]
            expected_data = expected_payload.get("data", [])

            stmt = await self.conn.prepare(TARGET_QUERIES["0.25"])
            columns = [attr.name for attr in stmt.get_attributes()]
            records = await stmt.fetch()

            user_data = []
            for r in records:
                user_data.append([serialize_record_val(r[col]) for col in columns])

            self.assertEqual(expected_data, user_data, "Task 0.25 expected_result data must match actual query execution")
            self.assertEqual(sorted(expected_data), sorted(user_data))
        finally:
            await users_conn.close()

    async def test_mission_2_and_task_1_3_match_users_db_expected_results(self):
        users_dsn = get_db_dsn("DATABASE_URL", "postgresql://postgres:postgres@localhost:5430/users_db")
        try:
            users_conn = await asyncio.wait_for(asyncpg.connect(users_dsn), timeout=10.0)
        except Exception as e:
            self.skipTest(f"users_db not reachable at {users_dsn} ({e})")

        test_tasks = [
            ("1.03", 1, 3),
            ("1.09", 1, 9),
            ("1.23", 1, 23),
            ("2.02", 2, 2),
            ("2.05", 2, 5),
            ("2.06", 2, 6),
            ("2.08", 2, 8),
            ("2.10", 2, 10),
            ("2.11", 2, 11),
            ("2.12", 2, 12),
        ]

        try:
            for task_code, mission_id, task_id in test_tasks:
                with self.subTest(task=task_code):
                    row = await users_conn.fetchrow(
                        "SELECT correct_query, expected_result FROM tasks WHERE mission_id = $1 AND task_id = $2;",
                        mission_id, task_id
                    )
                    self.assertIsNotNone(row, f"Task {task_code} should exist in tasks table")
                    self.assertIsNotNone(row["correct_query"], f"correct_query should not be NULL for task {task_code}")

                    expected_payload = json.loads(row["expected_result"]) if isinstance(row["expected_result"], str) else row["expected_result"]
                    expected_columns = expected_payload.get("columns", [])
                    expected_data = expected_payload.get("data", [])
                    expected_count = expected_payload.get("row_count", len(expected_data))

                    query = TARGET_QUERIES[task_code]
                    stmt = await self.conn.prepare(query)
                    columns = [attr.name for attr in stmt.get_attributes()]
                    records = await stmt.fetch()

                    user_data = []
                    for r in records:
                        user_data.append([serialize_record_val(r[col]) for col in columns])

                    self.assertEqual(columns, expected_columns, f"{task_code} columns mismatch")
                    self.assertEqual(user_data, expected_data, f"{task_code} data mismatch")
                    self.assertEqual(len(user_data), expected_count, f"{task_code} row count mismatch")
        finally:
            await users_conn.close()


if __name__ == "__main__":
    unittest.main()
