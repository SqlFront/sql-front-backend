--
-- Migration: 012_fix_tasks_2_11_and_2_12.sql
-- Feature: curriculum-and-tasks
-- Description: Clarify TRIM/FMMonth requirement in Task 2.11 and fix military unit duplication in Task 2.12 avg_efficiency
--

-- Task 2.11 (task_global_id = 83, «Сезонность боевых действий»)
UPDATE public.tasks
SET description = 'Для выявления сезонных закономерностей в боевых действиях проанализируйте все 12 месяцев года. Сгенерируйте календарь месяцев от 1 до 12 с их названиями. Подсчитайте общее количество завершившихся сражений (total_battles по end_date) и долю побед советских войск (win_percentage, округлённую до 1 знака после запятой) для каждого месяца. Победами считаются битвы с исходами, свидетельствующими об успехе СССР (содержащими корни «побед», «успеш», «освобожд», «разгром», «взятие», «капитуляц» и не относящимися к победам вермахта). Если в месяце не было боев, выведите 0 боев и 0.0% побед. Выведите month_num, month_name, total_battles, win_percentage с сортировкой по номеру месяца.

Поля в результирующей таблице: `month_num`, `month_name`, `total_battles`, `win_percentage`
Примечание: название месяца month_name должно быть на английском языке и не содержать пробелов-заполнителей (используйте TRIM(TO_CHAR(...)) или формат ''FMMonth'').',
    clue = 'Используйте generate_series(1, 12) для создания сетки месяцев и объедините через LEFT JOIN с группировкой битв по EXTRACT(MONTH FROM end_date). Для формирования month_name без концевых пробелов используйте TRIM(TO_CHAR(TO_DATE(m::text, ''MM''), ''Month'')) или TO_CHAR(..., ''FMMonth'').'
WHERE task_global_id = 83;

-- Task 2.12 (task_global_id = 62, «Стоимость победы»)
UPDATE public.tasks
SET clue = 'Чтобы избежать искажения средней боевой эффективности из-за разного числа бойцов и записей снаряжения в подразделениях, рассчитывайте avg_efficiency отдельно для воинских частей каждой битвы (через CTE или подзапрос по battle_military_unit и military_unit). Потери и снаряжение агрегируйте по бойцам, участвовавшим в битве. В основном запросе вычислите ранги DENSE_RANK() и cost_ratio = ROUND((losses / NULLIF(avg_efficiency, 0))::numeric, 2)::float.',
    correct_query = 'WITH battle_units AS (
    SELECT bmu.battle_id,
           ROUND(AVG(mu.combat_efficiency)::numeric, 1)::float AS avg_efficiency
    FROM battle_military_unit bmu
    JOIN military_unit mu ON bmu.unit_id = mu.id
    GROUP BY bmu.battle_id
),
battle_soldiers AS (
    SELECT b.id AS battle_id,
           b.battle_name,
           COUNT(DISTINCT s.id) FILTER (WHERE s.status IN (''убит'', ''пропал без вести''))::int AS losses,
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
ORDER BY cost_ratio DESC, battle_name;',
    expected_result = '{"columns": ["battle_name", "losses", "avg_efficiency", "equipment_used", "loss_rank", "eff_rank", "cost_ratio"], "data": [["Сталинградская битва", 2, 92.6, 6, 1, 9, 0.02], ["Балатонская операция", 1, 97.6, 1, 2, 3, 0.01], ["Битва за Воронеж", 1, 92.3, 6, 2, 10, 0.01], ["Битва за Днепр", 1, 94.4, 0, 2, 7, 0.01], ["Битва за Кавказ", 1, 96.7, 0, 2, 4, 0.01], ["Битва при Дебрецене", 1, 96.7, 0, 2, 4, 0.01], ["Блокада Ленинграда", 1, 75.0, 0, 2, 24, 0.01], ["Будапештская операция", 1, 96.7, 0, 2, 4, 0.01], ["Восточно-Прусская операция", 1, 87.2, 24, 2, 15, 0.01], ["Корсунь-Шевченковская операция", 1, 86.8, 2, 2, 16, 0.01], ["Ржевская битва", 1, 82.5, 121, 2, 18, 0.01], ["Харьковская операция", 1, 81.8, 0, 2, 20, 0.01], ["Берлинская операция", 0, 98.5, 1, 3, 1, 0.0], ["Битва за Берлин", 0, 98.2, 121, 3, 2, 0.0], ["Битва за Москву", 0, 88.0, 121, 3, 13, 0.0], ["Висло-Одерская операция", 0, 96.4, 120, 3, 5, 0.0], ["Демянская операция", 0, 78.0, 1, 3, 21, 0.0], ["Керченско-Эльтигенская операция", 0, 88.9, 0, 3, 12, 0.0], ["Курская битва", 0, 87.7, 4, 3, 14, 0.0], ["Маньчжурская операция", 0, 68.3, 0, 3, 26, 0.0], ["Оборона Брестской крепости", 0, 96.2, 0, 3, 6, 0.0], ["Оборона Брестской крепости", 0, 96.2, 0, 3, 6, 0.0], ["Оборона Заполярья", 0, 73.9, 0, 3, 25, 0.0], ["Оборона Севастополя", 0, 82.4, 0, 3, 19, 0.0], ["Оборона Тулы", 0, 85.2, 0, 3, 17, 0.0], ["Операция \"Багратион\"", 0, 92.8, 2, 3, 8, 0.0], ["Пражская операция", 0, 90.0, 0, 3, 11, 0.0], ["Прорыв блокады Ленинграда", 0, 75.2, 1, 3, 23, 0.0], ["Смоленское сражение", 0, 77.7, 121, 3, 22, 0.0], ["Таллинский переход", 0, 96.2, 0, 3, 6, 0.0]], "row_count": 30}'::jsonb
WHERE task_global_id = 62;
