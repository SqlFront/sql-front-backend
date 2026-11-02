--
-- Migration: 010_fix_tasks_1_9_and_1_23.sql
-- Feature: curriculum-and-tasks
-- Description: Fix artillery logistics calculation (Task 1.9) and Stalingrad loss filtering (Task 1.23)
--

-- Task 1.9 (task_global_id = 41, «Логистика артиллерии Сталинградского фронта»)
UPDATE public.tasks
SET description = 'Рассчитайте суммарный объем артиллерии и среднее количество артиллерийского вооружения на одного военнослужащего в частях, дислоцированных в Сталинграде.

Поля в результирующей таблице: `equipment_type`, `total`, `per_soldier`
Примечание: округленное до 2 знаков; Отфильтруйте данные по расположению части «Сталинград» (mu.location = ''Сталинград'') и типу вооружения «артиллерия» (e.equipment_type = ''артиллерия'').',
    clue = 'Используйте CTE или раздельные агрегации для подсчёта общего объёма артиллерии частей в Сталинграде и общего количества солдат в этих же частях, чтобы избежать эффекта размножения строк при JOIN. Затем разделите суммарное вооружение на число бойцов с округлением до 2 знаков.',
    correct_query = 'WITH stalingrad_artillery AS (
    SELECT e.equipment_type,
           SUM(e.quantity) AS total_qty
    FROM military_unit mu
    JOIN equipment e ON mu.id = e.unit_id
    WHERE mu.location = ''Сталинград'' AND e.equipment_type = ''артиллерия''
    GROUP BY e.equipment_type
),
stalingrad_soldiers AS (
    SELECT COUNT(DISTINCT ms.soldier_id) AS soldiers_count
    FROM military_service ms
    JOIN military_unit mu ON ms.unit_id = mu.id
    JOIN equipment e ON mu.id = e.unit_id
    WHERE mu.location = ''Сталинград'' AND e.equipment_type = ''артиллерия''
)
SELECT sa.equipment_type,
       sa.total_qty::int AS total,
       ROUND(sa.total_qty::numeric / NULLIF(ss.soldiers_count, 0), 2)::float AS per_soldier
FROM stalingrad_artillery sa
CROSS JOIN stalingrad_soldiers ss;',
    expected_result = '{"columns": ["equipment_type", "total", "per_soldier"], "data": [["артиллерия", 24, 8.0]], "row_count": 1}'::jsonb
WHERE task_global_id = 41;

-- Task 1.23 (task_global_id = 51, «Категории потерь под Сталинградом»)
UPDATE public.tasks
SET description = 'Оцените потери советских войск в Сталинградской битве. С помощью CTE выделите бойцов подразделений, участвовавших в Сталинградской битве (через battle_military_unit и battle), проходивших службу в период её проведения. Разделите потери на две категории: «Безвозвратные потери» (статус «убит» или «пропал без вести») и «Санитарные потери» (статус «ранен»), и объедините результаты через UNION ALL.

Поля в результирующей таблице: `loss_category`, `soldiers_count`',
    clue = 'Соедините soldier, military_service, battle_military_unit и battle с фильтром b.battle_name = ''Сталинградская битва'' и проверкой пересечения периодов службы с битвой: ms.start_date <= b.end_date AND (ms.end_date IS NULL OR ms.end_date >= b.start_date). Разделите потери через два CTE или FILTER и объедините с помощью UNION ALL.',
    correct_query = 'WITH stalingrad_soldiers AS (
    SELECT DISTINCT s.id, s.status
    FROM soldier s
    JOIN military_service ms ON s.id = ms.soldier_id
    JOIN battle_military_unit bmu ON ms.unit_id = bmu.unit_id
    JOIN battle b ON bmu.battle_id = b.id
    WHERE b.battle_name = ''Сталинградская битва''
      AND ms.start_date <= b.end_date
      AND (ms.end_date IS NULL OR ms.end_date >= b.start_date)
),
irrecoverable AS (
    SELECT ''Безвозвратные потери'' AS loss_category, COUNT(*)::int AS soldiers_count
    FROM stalingrad_soldiers
    WHERE status IN (''убит'', ''пропал без вести'')
),
sanitary AS (
    SELECT ''Санитарные потери'' AS loss_category, COUNT(*)::int AS soldiers_count
    FROM stalingrad_soldiers
    WHERE status = ''ранен''
)
SELECT loss_category, soldiers_count FROM irrecoverable
UNION ALL
SELECT loss_category, soldiers_count FROM sanitary;',
    expected_result = '{"columns": ["loss_category", "soldiers_count"], "data": [["Безвозвратные потери", 2], ["Санитарные потери", 1]], "row_count": 2}'::jsonb
WHERE task_global_id = 51;
