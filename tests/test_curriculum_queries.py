import asyncio
import json
from datetime import date, datetime
from decimal import Decimal
import unittest
import asyncpg


TARGET_QUERIES = {
    "0.10": """SELECT unit_name FROM military_unit WHERE unit_name NOT LIKE '%стрелков%';""",
    "0.11": """SELECT item_name FROM equipment WHERE item_name LIKE '____';""",
    "1.13": """SELECT s.full_name, u.unit_name, e.item_name, ea.quantity, ea.issue_date
FROM soldier s
JOIN military_service ms ON s.id = ms.soldier_id
JOIN military_unit u ON ms.unit_id = u.id
JOIN equipment_assignment ea ON s.id = ea.soldier_id
JOIN equipment e ON ea.equipment_id = e.id
ORDER BY s.full_name, ea.issue_date;""",
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
    SELECT s.id, s.status
    FROM soldier s
    JOIN military_service ms ON s.id = ms.soldier_id
    WHERE ms.start_date <= '1943-02-02'
      AND (ms.end_date IS NULL OR ms.end_date >= '1942-07-17')
),
irrecoverable AS (
    SELECT 'Безвозвратные потери' AS loss_category, COUNT(*) AS soldiers_count
    FROM stalingrad_soldiers
    WHERE status IN ('убит', 'пропал без вести')
),
sanitary AS (
    SELECT 'Санитарные потери' AS loss_category, COUNT(*) AS soldiers_count
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
}


def serialize_record_val(val):
    if isinstance(val, (date, datetime)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    return val


class TestCurriculumQueries(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.conn = await asyncpg.connect("postgresql://sql_runner:secret@localhost:5430/game_db")

    async def asyncTearDown(self):
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


if __name__ == "__main__":
    unittest.main()
