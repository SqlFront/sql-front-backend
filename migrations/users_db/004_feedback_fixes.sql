--
-- Migration: 004_feedback_fixes.sql
-- Feature: curriculum-task-validation-fixes
-- Description: Fix expected_result, correct_query, descriptions and output column standards for tasks 0.13, 1.1, 1.4, 1.9, 1.17, 5.2 based on student feedback
--

-- Task 0.13 (task_global_id = 14, «Сила в единстве»)
UPDATE public.tasks
SET title = 'Сила в единстве',
    description = 'Подсчитайте количество солдат в каждой воинской части и выведите названия этих подразделений. Это покажет, какие формирования были наиболее многочисленными.

Формат результата (столбцы строго в указанном порядке):
1. unit_name — название воинской части;
2. total_soldiers — количество солдат в подразделении.

Отсортируйте результат по названию части (unit_name) в алфавитном порядке.',
    clue = 'Используйте JOIN между military_unit и military_service, сгруппируйте по mu.unit_name, выведите SELECT mu.unit_name, COUNT(ms.soldier_id) AS total_soldiers ORDER BY mu.unit_name;',
    correct_query = 'SELECT mu.unit_name, COUNT(ms.soldier_id) AS total_soldiers
FROM military_unit mu
JOIN military_service ms ON mu.id = ms.unit_id
GROUP BY mu.unit_name
ORDER BY mu.unit_name;',
    expected_result = '{"columns": ["unit_name", "total_soldiers"], "data": [["1-й отдельный чехословацкий батальон", 2], ["1-й чехословацкий отдельный батальон", 1], ["1-я гвардейская танковая армия", 2], ["1-я морская бригада", 1], ["101-й инженерно-сапёрный батальон", 2], ["101-й полк НКВД", 1], ["101-й учебный полк", 1], ["106-я стрелковая дивизия", 1], ["14-я отдельная штрафная рота", 1], ["150-я стрелковая дивизия", 2], ["16-я воздушная армия", 2], ["18-я дивизия СС \"Хорст Вессель\"", 1], ["2-я ударная армия", 1], ["225-й отдельный инженерный батальон", 1], ["28-я дивизия народного ополчения", 1], ["3-я воздушная армия", 1], ["316-я стрелковая дивизия", 2], ["369-й отдельный батальон морской пехоты", 1], ["37-й гвардейский миномётный полк", 1], ["46-й гвардейский ночной бомбардировочный полк", 2], ["585-й женский авиаполк", 1], ["62-я армия", 3], ["64-я стрелковая дивизия", 2], ["8-я гвардейская армия", 1], ["88-й отдельный лыжный батальон", 1], ["Отдельная медико-санитарная рота", 1], ["Отдельный батальон связи №45", 1], ["Отдельный отряд собак-истребителей танков", 1], ["Отдельный отряд собак-миноискателей", 2]], "row_count": 29}'::jsonb
WHERE task_global_id = 14;

-- Task 1.1 (task_global_id = 37, «Логистика Сталинградской битвы»)
UPDATE public.tasks
SET title = 'Логистика Сталинградской битвы',
    description = 'Определите общее количество боеприпасов (строго тип снаряжения: «боеприпасы»), выделенных каждой воинской части в Сталинграде. Это поможет оценить обеспеченность войск в критический период обороны.

Формат результата (столбцы строго в указанном порядке):
1. unit_id — уникальный идентификатор воинской части;
2. total_ammo — суммарное количество боеприпасов (сумма quantity).

Отсортируйте результат по возрастанию unit_id.',
    clue = 'Используйте JOIN между military_unit и equipment с фильтром mu.location = ''Сталинград'' AND e.equipment_type = ''боеприпасы'', сгруппируйте по mu.id и добавьте ORDER BY mu.id;',
    correct_query = 'SELECT mu.id AS unit_id, SUM(e.quantity) AS total_ammo
FROM military_unit mu
JOIN equipment e ON mu.id = e.unit_id
WHERE mu.location = ''Сталинград'' AND e.equipment_type = ''боеприпасы''
GROUP BY mu.id
ORDER BY mu.id;',
    expected_result = '{"columns": ["unit_id", "total_ammo"], "data": [[2, 50000], [13, 30000], [18, 40000], [21, 50000], [26, 70000]], "row_count": 5}'::jsonb
WHERE task_global_id = 37;

-- Task 1.4 (task_global_id = 39, «Анализ эффективности частей»)
UPDATE public.tasks
SET title = 'Анализ эффективности частей',
    description = 'Выведите для каждого военного подразделения его исходную и скорректированную боевую эффективность. Корректировка рассчитывается путем уменьшения исходного показателя (combat_efficiency) пропорционально доле безвозвратных потерь (статусы «убит» и «пропал без вести») от общей численности личного состава подразделения.

Формат результата (столбцы строго в указанном порядке):
1. unit_name — название подразделения;
2. initial_efficiency — исходная боевая эффективность подразделения;
3. loss_percentage — процент безвозвратных потерь личного состава (округленный до 2 знаков);
4. adjusted_efficiency — скорректированная боевая эффективность (округленная до 2 знаков).

Отсортируйте результат по убыванию initial_efficiency (combat_efficiency), а затем по алфавиту unit_name.',
    clue = 'Сгруппируйте солдат по подразделениям. Для подсчета потерь используйте условную агрегацию: COUNT(CASE WHEN s.status IN (''убит'', ''пропал без вести'') THEN 1 END). Процент потерь равен ROUND(100.0 * потери / всего, 2). Скорректированная эффективность равна ROUND(combat_efficiency * (1.0 - 1.0 * потери / всего), 2).',
    correct_query = 'SELECT mu.unit_name,
       mu.combat_efficiency AS initial_efficiency,
       ROUND(100.0 * COUNT(CASE WHEN s.status IN (''убит'', ''пропал без вести'') THEN 1 END) / COUNT(s.id), 2) AS loss_percentage,
       ROUND(mu.combat_efficiency * (1.0 - 1.0 * COUNT(CASE WHEN s.status IN (''убит'', ''пропал без вести'') THEN 1 END) / COUNT(s.id)), 2) AS adjusted_efficiency
FROM military_unit mu
JOIN military_service ms ON ms.unit_id = mu.id
JOIN soldier s ON s.id = ms.soldier_id
GROUP BY mu.id, mu.unit_name, mu.combat_efficiency
ORDER BY mu.combat_efficiency DESC, mu.unit_name;',
    expected_result = '{"columns": ["unit_name", "initial_efficiency", "loss_percentage", "adjusted_efficiency"], "data": [["8-я гвардейская армия", 98.5, 0.0, 98.5], ["150-я стрелковая дивизия", 97.8, 50.0, 48.9], ["46-й гвардейский ночной бомбардировочный полк", 96.7, 50.0, 48.35], ["37-й гвардейский миномётный полк", 96.5, 100.0, 0.0], ["101-й полк НКВД", 96.2, 100.0, 0.0], ["1-я гвардейская танковая армия", 95.0, 50.0, 47.5], ["585-й женский авиаполк", 94.1, 100.0, 0.0], ["64-я стрелковая дивизия", 92.4, 0.0, 92.4], ["62-я армия", 92.3, 33.33, 61.53], ["Отдельная медико-санитарная рота", 91.7, 100.0, 0.0], ["225-й отдельный инженерный батальон", 89.7, 100.0, 0.0], ["101-й инженерно-сапёрный батальон", 89.5, 50.0, 44.75], ["106-я стрелковая дивизия", 89.3, 100.0, 0.0], ["16-я воздушная армия", 88.9, 0.0, 88.9], ["369-й отдельный батальон морской пехоты", 88.9, 0.0, 88.9], ["18-я дивизия СС \"Хорст Вессель\"", 88.1, 0.0, 88.1], ["316-я стрелковая дивизия", 85.5, 50.0, 42.75], ["Отдельный батальон связи №45", 85.2, 0.0, 85.2], ["1-й отдельный чехословацкий батальон", 85.0, 100.0, 0.0], ["3-я воздушная армия", 85.0, 100.0, 0.0], ["1-я морская бригада", 82.4, 0.0, 82.4], ["Отдельный отряд собак-истребителей танков", 82.4, 0.0, 82.4], ["Отдельный отряд собак-миноискателей", 81.3, 0.0, 81.3], ["1-й чехословацкий отдельный батальон", 78.5, 0.0, 78.5], ["2-я ударная армия", 75.2, 0.0, 75.2], ["88-й отдельный лыжный батальон", 73.9, 0.0, 73.9], ["28-я дивизия народного ополчения", 69.8, 100.0, 0.0], ["101-й учебный полк", 68.3, 0.0, 68.3], ["14-я отдельная штрафная рота", 65.8, 0.0, 65.8]], "row_count": 29}'::jsonb
WHERE task_global_id = 39;

-- Task 1.9 (task_global_id = 41, «Логистика артиллерии Сталинградского фронта»)
UPDATE public.tasks
SET title = 'Логистика артиллерии Сталинградского фронта',
    description = 'Рассчитайте суммарный объем артиллерии и среднее количество артиллерийского вооружения на одного военнослужащего в частях, дислоцированных в Сталинграде.

Формат результата (столбцы строго в указанном порядке):
1. equipment_type — тип снаряжения («артиллерия»);
2. total — суммарное количество единиц артиллерии (сумма quantity);
3. per_soldier — среднее количество артиллерии на одного бойца (округленное до 2 знаков через AVG(e.quantity)).

Отфильтруйте данные по расположению части «Сталинград» (mu.location = ''Сталинград'') и типу вооружения «артиллерия» (e.equipment_type = ''артиллерия'').',
    clue = 'Используйте JOIN между military_unit, equipment, military_service и soldier с фильтром mu.location = ''Сталинград'' AND e.equipment_type = ''артиллерия''. Сгруппируйте по e.equipment_type и рассчитайте SUM(e.quantity) AS total, ROUND(AVG(e.quantity), 2) AS per_soldier;',
    correct_query = 'SELECT e.equipment_type,
       SUM(e.quantity) AS total,
       ROUND(AVG(e.quantity), 2) AS per_soldier
FROM military_unit mu
JOIN equipment e ON mu.id = e.unit_id
JOIN military_service ms ON mu.id = ms.unit_id
JOIN soldier s ON ms.soldier_id = s.id
WHERE mu.location = ''Сталинград'' AND e.equipment_type = ''артиллерия''
GROUP BY e.equipment_type;',
    expected_result = '{"columns": ["equipment_type", "total", "per_soldier"], "data": [["артиллерия", 72, 24.0]], "row_count": 1}'::jsonb
WHERE task_global_id = 41;

-- Task 1.17 (task_global_id = 44, «Участники Сталинграда»)
UPDATE public.tasks
SET title = 'Участники Сталинграда',
    description = 'Найдите всех солдат, служивших в частях, дислоцированных в Сталинграде (location = ''Сталинград''). Это основа для создания мемориальных списков.

Формат результата:
1. full_name — полное имя бойца (уникальные значения без повторов через DISTINCT).

Отсортируйте результат по алфавиту full_name.',
    clue = 'Используйте SELECT DISTINCT s.full_name FROM soldier s JOIN military_service ms ON s.id = ms.soldier_id WHERE ms.unit_id IN (SELECT id FROM military_unit WHERE location = ''Сталинград'') ORDER BY s.full_name;',
    correct_query = 'SELECT DISTINCT s.full_name
FROM soldier s
JOIN military_service ms ON s.id = ms.soldier_id
WHERE ms.unit_id IN (
    SELECT id FROM military_unit WHERE location = ''Сталинград''
)
ORDER BY s.full_name;',
    expected_result = '{"columns": ["full_name"], "data": [["Павлов Яков Фёдорович"], ["Петров Дмитрий Иванович"], ["Смирнов Василий Иванович"], ["Смирнова Анна Васильевна"], ["Соколовская Надежда Викторовна"], ["Ткаченко Григорий Петрович"], ["Ткаченко Иван Григорьевич"], ["Фёдоров Игорь Васильевич"]], "row_count": 8}'::jsonb
WHERE task_global_id = 44;

-- Task 5.2 (task_global_id = 107, «Бойцы подразделения»)
UPDATE public.tasks
SET title = 'Бойцы подразделения',
    description = 'Напишите табличную функцию get_unit_soldiers(p_unit_name VARCHAR), возвращающую список бойцов, служивших в указанной воинской части.

Формат возвращаемой таблицы (столбцы строго в указанном порядке):
1. full_name (VARCHAR) — полное имя солдата;
2. enlistment_city (VARCHAR) — город призыва солдата.',
    clue = 'Используйте RETURNS TABLE (full_name VARCHAR, enlistment_city VARCHAR) и RETURN QUERY SELECT s.full_name, s.enlistment_city FROM soldier s JOIN military_service ms ON s.id = ms.soldier_id JOIN military_unit mu ON ms.unit_id = mu.id WHERE mu.unit_name = p_unit_name;',
    correct_query = 'CREATE OR REPLACE FUNCTION get_unit_soldiers(p_unit_name VARCHAR) RETURNS TABLE (full_name VARCHAR, enlistment_city VARCHAR) AS $$ BEGIN RETURN QUERY SELECT s.full_name, s.enlistment_city FROM soldier s JOIN military_service ms ON s.id = ms.soldier_id JOIN military_unit mu ON ms.unit_id = mu.id WHERE mu.unit_name = p_unit_name; END; $$ LANGUAGE plpgsql;',
    expected_result = '{"mode": "ddl", "test_query": "SELECT * FROM get_unit_soldiers(''1-я морская бригада'') ORDER BY full_name;", "columns": ["full_name", "enlistment_city"], "data": [["Волкова Елена Сергеевна", "Горький"]]}'::jsonb
WHERE task_global_id = 107;
