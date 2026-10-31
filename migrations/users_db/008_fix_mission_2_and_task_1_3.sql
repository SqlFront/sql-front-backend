--
-- Migration: 008_fix_mission_2_and_task_1_3.sql
-- Feature: curriculum-and-tasks
-- Description: Authentic analytics for Mission 2 and Task 1.3 based on battle_military_unit
--

-- Task 1.3 (task_global_id = 38, «Поиск героев для награждения»)
UPDATE public.tasks
SET description = 'Выявите 20 солдат, участвовавших в наибольшем количестве сражений, и присвойте им ранги. Вычисленные столбцы назовите battles_participated и hero_rank. Это основа для награждения орденами и медалями.

Формат результата (столбцы строго в указанном порядке):
1. full_name — полное имя бойца;
2. battles_participated — количество сражений, в которых участвовал боец;
3. hero_rank — ранг бойца по числу сражений через DENSE_RANK().',
    clue = 'Соедините soldier, military_service, battle_military_unit и battle. Проверьте периоды службы: ms.start_date <= b.end_date AND (ms.end_date IS NULL OR ms.end_date >= b.start_date). Примените DENSE_RANK() OVER (ORDER BY COUNT(DISTINCT b.id) DESC, s.full_name) и ограничьте вывод 20 записями.',
    correct_query = 'SELECT s.full_name,
       COUNT(DISTINCT b.id) AS battles_participated,
       DENSE_RANK() OVER (ORDER BY COUNT(DISTINCT b.id) DESC, s.full_name) AS hero_rank
FROM soldier s
JOIN military_service ms ON s.id = ms.soldier_id
JOIN battle_military_unit bmu ON ms.unit_id = bmu.unit_id
JOIN battle b ON bmu.battle_id = b.id
WHERE ms.start_date <= b.end_date AND (ms.end_date IS NULL OR ms.end_date >= b.start_date)
GROUP BY s.full_name
ORDER BY hero_rank
LIMIT 20;',
    expected_result = '{"columns": ["full_name", "battles_participated", "hero_rank"], "data": [["Жуковский Виктор Михайлович", 4, 1], ["Орлова Вера Павловна", 4, 2], ["Беляев Павел Дмитриевич", 3, 3], ["Громова Екатерина Ивановна", 3, 4], ["Иванов Алексей Петрович", 3, 5], ["Громов Михаил Сергеевич", 2, 6], ["Зайцева Людмила Михайловна", 2, 7], ["Кузнецов Пётр Васильевич", 2, 8], ["Павлов Яков Фёдорович", 2, 9], ["Петров Дмитрий Иванович", 2, 10], ["Смирнова Анна Васильевна", 2, 11], ["Белов Дмитрий Николаевич", 1, 12], ["Горбачёв Алексей Дмитриевич", 1, 13], ["Жуков Андрей Григорьевич", 1, 14], ["Жукова Елена Викторовна", 1, 15], ["Ковалёв Сергей Николаевич", 1, 16], ["Ковалёва Ольга Дмитриевна", 1, 17], ["Козлов Николай Семёнович", 1, 18], ["Кузнецов Артём Игоревич", 1, 19], ["Морозов Иван Кузьмич", 1, 20]], "row_count": 20}'::jsonb
WHERE task_global_id = 38;

-- Task 2.2 (task_global_id = 78, «Сравнение стратегий»)
UPDATE public.tasks
SET description = 'Сравните среднюю боевую эффективность частей, участвовавших в стратегических и локальных операциях. К стратегическим операциям относятся битвы с уровнем важности «стратегическая», к локальным — все остальные («фронтовая», «тактическая»).

Формат результата (столбцы строго в указанном порядке):
1. battle_group — группа операций («Стратегические битвы» или «Локальные операции»);
2. avg_efficiency — средняя боевая эффективность задействованных подразделений (округленная до 2 знаков).',
    clue = 'Примените CASE WHEN b.importance_level = ''стратегическая'' THEN ''Стратегические битвы'' ELSE ''Локальные операции'' END для группировки битв. Соедините battle, battle_military_unit и military_unit и вычислите ROUND(AVG(mu.combat_efficiency)::numeric, 2)::float.',
    correct_query = 'SELECT CASE 
           WHEN b.importance_level = ''стратегическая'' THEN ''Стратегические битвы'' 
           ELSE ''Локальные операции'' 
       END AS battle_group,
       ROUND(AVG(mu.combat_efficiency)::numeric, 2)::float AS avg_efficiency
FROM battle b
JOIN battle_military_unit bmu ON b.id = bmu.battle_id
JOIN military_unit mu ON bmu.unit_id = mu.id
GROUP BY battle_group
ORDER BY battle_group DESC;',
    expected_result = '{"columns": ["battle_group", "avg_efficiency"], "data": [["Стратегические битвы", 90.15], ["Локальные операции", 85.15]], "row_count": 2}'::jsonb
WHERE task_global_id = 78;

-- Task 2.5 (task_global_id = 81, «Живучесть подразделений»)
UPDATE public.tasks
SET description = 'Для каждого воинского подразделения рассчитайте: общую продолжительность участия в боях (разница между датой окончания последнего и датой начала первого боя), количество боёв, в которых оно участвовало, и количество солдат с безвозвратными потерями («убит», «пропал без вести»). На основе этих данных вычислите среднее количество потерь на один бой и процентиль подразделения по продолжительности участия в боях через PERCENT_RANK() по убыванию total_duration.

Формат результата (столбцы строго в указанном порядке):
1. unit_name — название воинского подразделения;
2. total_duration — общая продолжительность участия в боях (в днях);
3. battles_count — количество сражений с участием подразделения;
4. losses — количество безвозвратных потерь личного состава;
5. loss_per_battle_ratio — среднее количество потерь на один бой (округленное до 2 знаков);
6. survival_percentile — процентиль по продолжительности через PERCENT_RANK().',
    clue = 'Сгруппируйте данные по подразделениям. Для продолжительности используйте MAX(b.end_date) - MIN(b.start_date). Потери считайте через COUNT(DISTINCT s.id) FILTER (WHERE s.status IN (''убит'', ''пропал без вести'')). Средние потери вычислите делением потерь на количество боёв с округлением до 2 знаков. Для процентиля примените PERCENT_RANK() OVER (ORDER BY (MAX(b.end_date) - MIN(b.start_date)) DESC). Отсортируйте результат по убыванию total_duration, затем по unit_name.',
    correct_query = 'SELECT mu.unit_name,
       (MAX(b.end_date) - MIN(b.start_date))::int AS total_duration,
       COUNT(DISTINCT b.id)::int AS battles_count,
       COUNT(DISTINCT s.id) FILTER (WHERE s.status IN (''убит'', ''пропал без вести''))::int AS losses,
       ROUND((COUNT(DISTINCT s.id) FILTER (WHERE s.status IN (''убит'', ''пропал без вести'')))::numeric / NULLIF(COUNT(DISTINCT b.id), 0), 2)::float AS loss_per_battle_ratio,
       PERCENT_RANK() OVER (ORDER BY (MAX(b.end_date) - MIN(b.start_date)) DESC)::float AS survival_percentile
FROM military_unit mu
JOIN battle_military_unit bmu ON mu.id = bmu.unit_id
JOIN battle b ON bmu.battle_id = b.id
LEFT JOIN military_service ms ON mu.id = ms.unit_id
LEFT JOIN soldier s ON ms.soldier_id = s.id
GROUP BY mu.id, mu.unit_name
ORDER BY total_duration DESC, mu.unit_name;',
    expected_result = '{"columns": ["unit_name", "total_duration", "battles_count", "losses", "loss_per_battle_ratio", "survival_percentile"], "data": [["88-й отдельный лыжный батальон", 1190, 3, 0, 0.0, 0.0], ["1-й отдельный чехословацкий батальон", 1176, 3, 2, 0.67, 0.034482758620689655], ["46-й гвардейский ночной бомбардировочный полк", 964, 4, 1, 0.25, 0.06896551724137931], ["28-я дивизия народного ополчения", 931, 2, 1, 0.5, 0.10344827586206896], ["Отдельный отряд собак-миноискателей", 871, 1, 0, 0.0, 0.13793103448275862], ["101-й полк НКВД", 647, 4, 1, 0.25, 0.1724137931034483], ["1-й чехословацкий отдельный батальон", 646, 2, 0, 0.0, 0.20689655172413793], ["316-я стрелковая дивизия", 629, 3, 1, 0.33, 0.2413793103448276], ["62-я армия", 543, 3, 1, 0.33, 0.27586206896551724], ["1-я гвардейская танковая армия", 473, 4, 1, 0.25, 0.3103448275862069], ["14-я отдельная штрафная рота", 447, 1, 0, 0.0, 0.3448275862068966], ["2-я ударная армия", 344, 2, 0, 0.0, 0.3793103448275862], ["8-я гвардейская армия", 319, 4, 0, 0.0, 0.41379310344827586], ["3-я воздушная армия", 306, 2, 1, 0.5, 0.4482758620689655], ["1-я морская бригада", 247, 1, 0, 0.0, 0.4827586206896552], ["7-я гвардейская миномётная дивизия", 202, 1, 0, 0.0, 0.5172413793103449], ["585-й женский авиаполк", 200, 1, 1, 1.0, 0.5517241379310345], ["64-я стрелковая дивизия", 200, 1, 0, 0.0, 0.5517241379310345], ["Отдельная медико-санитарная рота", 200, 1, 1, 1.0, 0.5517241379310345], ["37-й гвардейский миномётный полк", 119, 1, 1, 1.0, 0.6551724137931034], ["150-я стрелковая дивизия", 116, 2, 1, 0.5, 0.6896551724137931], ["106-я стрелковая дивизия", 102, 1, 1, 1.0, 0.7241379310344828], ["101-й инженерно-сапёрный батальон", 49, 1, 1, 1.0, 0.7586206896551724], ["16-я воздушная армия", 49, 1, 0, 0.0, 0.7586206896551724], ["18-я дивизия СС \"Хорст Вессель\"", 49, 1, 0, 0.0, 0.7586206896551724], ["225-й отдельный инженерный батальон", 49, 1, 1, 1.0, 0.7586206896551724], ["Отдельный отряд собак-истребителей танков", 49, 1, 0, 0.0, 0.7586206896551724], ["Отдельный батальон связи №45", 42, 1, 0, 0.0, 0.9310344827586207], ["369-й отдельный батальон морской пехоты", 41, 1, 0, 0.0, 0.9655172413793104], ["101-й учебный полк", 24, 1, 0, 0.0, 1.0]], "row_count": 30}'::jsonb
WHERE task_global_id = 81;

-- Task 2.6 (task_global_id = 80, «Полный портрет части»)
UPDATE public.tasks
SET description = 'Сформируйте сводку по каждой воинской части: общее количество солдат, разнообразие типов снаряжения, количество сражений, в которых участвовала часть, и перечень полученных наград бойцами через запятую (или «Нет», если наград нет). Отсортируйте результат по убыванию количества солдат, а затем по названию части.

Формат результата (столбцы строго в указанном порядке):
1. unit_name — название воинской части;
2. soldiers_total — общее количество солдат в части;
3. equipment_types — количество уникальных типов снаряжения;
4. battles_participated — количество сражений, в которых участвовала часть;
5. medals_received — список уникальных наград бойцов через запятую по алфавиту (или «Нет»).',
    clue = 'Используйте LEFT JOIN подразделения с military_service, equipment, battle_military_unit и цепочкой soldier_medal -> medal. Примените COUNT(DISTINCT ...) для подсчёта уникальных солдат, типов снаряжения и битв части (bmu.battle_id). Для наград примените COALESCE(STRING_AGG(DISTINCT m.medal_name, '', '' ORDER BY m.medal_name), ''Нет'').',
    correct_query = 'SELECT mu.unit_name,
       COUNT(DISTINCT ms.soldier_id)::int AS soldiers_total,
       COUNT(DISTINCT e.equipment_type)::int AS equipment_types,
       COUNT(DISTINCT bmu.battle_id)::int AS battles_participated,
       COALESCE(STRING_AGG(DISTINCT m.medal_name, '', '' ORDER BY m.medal_name), ''Нет'') AS medals_received
FROM military_unit mu
LEFT JOIN military_service ms ON mu.id = ms.unit_id
LEFT JOIN equipment e ON mu.id = e.unit_id
LEFT JOIN battle_military_unit bmu ON mu.id = bmu.unit_id
LEFT JOIN soldier_medal sm ON ms.soldier_id = sm.soldier_id
LEFT JOIN medal m ON sm.medal_id = m.id
GROUP BY mu.id, mu.unit_name
ORDER BY soldiers_total DESC, mu.unit_name;',
    expected_result = '{"columns": ["unit_name", "soldiers_total", "equipment_types", "battles_participated", "medals_received"], "data": [["62-я армия", 3, 3, 3, "Герой Советского Союза, Медаль \"За взятие Берлина\", Орден Отечественной войны"], ["1-й отдельный чехословацкий батальон", 2, 0, 3, "Нет"], ["1-я гвардейская танковая армия", 2, 1, 4, "Герой Советского Союза"], ["101-й инженерно-сапёрный батальон", 2, 0, 1, "Нет"], ["150-я стрелковая дивизия", 2, 1, 2, "Медаль \"За оборону Сталинграда\", Медаль \"За отвагу\""], ["16-я воздушная армия", 2, 1, 1, "Медаль \"За оборону Москвы\", Орден Красной Звезды"], ["316-я стрелковая дивизия", 2, 3, 3, "Медаль \"За отвагу\""], ["46-й гвардейский ночной бомбардировочный полк", 2, 0, 4, "Нет"], ["64-я стрелковая дивизия", 2, 1, 1, "Нет"], ["Отдельный отряд собак-миноискателей", 2, 0, 1, "Нет"], ["1-й чехословацкий отдельный батальон", 1, 0, 2, "Нет"], ["1-я морская бригада", 1, 2, 1, "Нет"], ["101-й полк НКВД", 1, 0, 4, "Нет"], ["101-й учебный полк", 1, 0, 1, "Нет"], ["106-я стрелковая дивизия", 1, 1, 1, "Медаль \"Партизану Отечественной войны\""], ["14-я отдельная штрафная рота", 1, 0, 1, "Нет"], ["18-я дивизия СС \"Хорст Вессель\"", 1, 0, 1, "Нет"], ["2-я ударная армия", 1, 1, 2, "Орден Отечественной войны"], ["225-й отдельный инженерный батальон", 1, 0, 1, "Нет"], ["28-я дивизия народного ополчения", 1, 0, 2, "Нет"], ["3-я воздушная армия", 1, 1, 2, "Орден Красной Звезды"], ["369-й отдельный батальон морской пехоты", 1, 0, 1, "Нет"], ["37-й гвардейский миномётный полк", 1, 1, 1, "Нет"], ["585-й женский авиаполк", 1, 1, 1, "Нет"], ["8-я гвардейская армия", 1, 1, 4, "Орден Славы"], ["88-й отдельный лыжный батальон", 1, 0, 3, "Нет"], ["Отдельная медико-санитарная рота", 1, 2, 1, "Нет"], ["Отдельный батальон связи №45", 1, 0, 1, "Нет"], ["Отдельный отряд собак-истребителей танков", 1, 0, 1, "Нет"], ["7-я гвардейская миномётная дивизия", 0, 2, 1, "Нет"]], "row_count": 30}'::jsonb
WHERE task_global_id = 80;

-- Task 2.8 (task_global_id = 60, «Топ вражеских частей»)
UPDATE public.tasks
SET description = 'Для анализа тактики противника определите три вражеских подразделения, одержавших победы в сражениях с участием советских войск. Победами противника считаются сражения, в которых результат указывает на победу вермахта или потерю города (фильтр b.result ~* ''(победа вермахта|потеря города)''). Для каждого такого вражеского подразделения подсчитайте количество побед и суммарные безвозвратные потери советских войск («убит», «пропал без вести») в этих боях. Выведите unit_name, victories и total_soviet_losses по убыванию victories, затем по убыванию total_soviet_losses и названию подразделения.

Формат результата (столбцы строго в указанном порядке):
1. unit_name — название вражеского подразделения;
2. victories — количество одержанных побед;
3. total_soviet_losses — суммарные безвозвратные потери советских войск в этих сражениях.',
    clue = 'Соедините enemy_unit, battle_enemy_unit, battle, battle_military_unit, military_service и soldier. Отфильтруйте битвы с исходами побед противника (WHERE b.result ~* ''(победа вермахта|потеря города)''). Подсчитайте COUNT(DISTINCT b.id) как victories и потери советских бойцов COUNT(DISTINCT s.id) FILTER (WHERE s.status IN (''убит'', ''пропал без вести''))::float AS total_soviet_losses. Ограничьте вывод 3 записями (LIMIT 3).',
    correct_query = 'WITH enemy_battles AS (
    SELECT eu.unit_name,
           COUNT(DISTINCT b.id)::int AS victories,
           COUNT(DISTINCT s.id) FILTER (WHERE s.status IN (''убит'', ''пропал без вести''))::float AS total_soviet_losses
    FROM enemy_unit eu
    JOIN battle_enemy_unit beu ON eu.id = beu.enemy_unit_id
    JOIN battle b ON beu.battle_id = b.id
    JOIN battle_military_unit bmu ON b.id = bmu.battle_id
    LEFT JOIN military_service ms ON bmu.unit_id = ms.unit_id 
         AND ms.start_date <= b.end_date AND (ms.end_date IS NULL OR ms.end_date >= b.start_date)
    LEFT JOIN soldier s ON ms.soldier_id = s.id
    WHERE b.result ~* ''(победа вермахта|потеря города)''
    GROUP BY eu.id, eu.unit_name
)
SELECT unit_name, victories, total_soviet_losses
FROM enemy_battles
ORDER BY victories DESC, total_soviet_losses DESC, unit_name
LIMIT 3;',
    expected_result = '{"columns": ["unit_name", "victories", "total_soviet_losses"], "data": [["299-я пехотная дивизия", 1, 1.0], ["9-я армия", 1, 1.0], ["11-я армия", 1, 0.0]], "row_count": 3}'::jsonb
WHERE task_global_id = 60;

-- Task 2.10 (task_global_id = 61, «Эффективность наград»)
UPDATE public.tasks
SET description = 'Для оценки соответствия воинских наград реальным результатам в бою сопоставьте для каждого подразделения полученные награды с реальными победами и потерями. Победоносными считаются битвы с исходами побед советских войск (фильтр b.result ~* ''(побед|успеш|освобожд|разгром|взятие|капитуляц)'' AND b.result !~* ''вермахт''). Рассчитайте число награждений (awarded), число погибших и пропавших без вести бойцов подразделения (deaths), число побед подразделения (victories), соотношение побед к числу наград (victory_per_medal) и потерь к числу наград (death_per_medal). Отсортируйте результат: строки с нулевыми победами поместите в конец, затем по убыванию victory_per_medal, названию части и названию награды.

Формат результата (столбцы строго в указанном порядке):
1. unit_name — название воинского подразделения;
2. medal_name — название награды;
3. awarded — количество награжденных бойцов подразделения;
4. deaths — число погибших и пропавших без вести солдат;
5. victories — число победоносных боев;
6. victory_per_medal — соотношение побед к числу наград;
7. death_per_medal — соотношение потерь к числу наград.',
    clue = 'Используйте CTE. В первом CTE подсчитайте победы подразделения (фильтр b.result) и безвозвратные потери (status IN (''убит'', ''пропал без вести'')). Во втором CTE подсчитайте число награждений по каждой награде. В основном запросе вычислите victory_per_medal и death_per_medal через ROUND(...::numeric / NULLIF(awarded, 0), 2)::float. В ORDER BY используйте CASE WHEN victories = 0 THEN 1 ELSE 0 END, victory_per_medal DESC.',
    correct_query = 'WITH unit_stats AS (
    SELECT mu.id AS unit_id,
           mu.unit_name,
           COUNT(DISTINCT b.id) FILTER (WHERE b.result ~* ''(побед|успеш|освобожд|разгром|взятие|капитуляц)'' AND b.result !~* ''вермахт'')::int AS victories,
           COUNT(DISTINCT s.id) FILTER (WHERE s.status IN (''убит'', ''пропал без вести''))::int AS deaths
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
ORDER BY CASE WHEN us.victories = 0 THEN 1 ELSE 0 END, victory_per_medal DESC, us.unit_name, um.medal_name;',
    expected_result = '{"columns": ["unit_name", "medal_name", "awarded", "deaths", "victories", "victory_per_medal", "death_per_medal"], "data": [["1-я гвардейская танковая армия", "Герой Советского Союза", 1, 1, 3, 3.0, 1.0], ["8-я гвардейская армия", "Орден Славы", 1, 0, 3, 3.0, 0.0], ["150-я стрелковая дивизия", "Медаль \"За оборону Сталинграда\"", 1, 1, 2, 2.0, 1.0], ["150-я стрелковая дивизия", "Медаль \"За отвагу\"", 1, 1, 2, 2.0, 1.0], ["62-я армия", "Герой Советского Союза", 1, 1, 2, 2.0, 1.0], ["62-я армия", "Медаль \"За взятие Берлина\"", 1, 1, 2, 2.0, 1.0], ["62-я армия", "Орден Отечественной войны", 1, 1, 2, 2.0, 1.0], ["16-я воздушная армия", "Медаль \"За оборону Москвы\"", 1, 0, 1, 1.0, 0.0], ["16-я воздушная армия", "Орден Красной Звезды", 1, 0, 1, 1.0, 0.0], ["3-я воздушная армия", "Орден Красной Звезды", 1, 1, 1, 1.0, 1.0], ["316-я стрелковая дивизия", "Медаль \"За отвагу\"", 1, 1, 1, 1.0, 1.0], ["106-я стрелковая дивизия", "Медаль \"Партизану Отечественной войны\"", 1, 1, 0, 0.0, 1.0], ["2-я ударная армия", "Орден Отечественной войны", 1, 0, 0, 0.0, 0.0]], "row_count": 13}'::jsonb
WHERE task_global_id = 61;

-- Task 2.12 (task_global_id = 62, «Стоимость победы»)
UPDATE public.tasks
SET description = 'Для анализа ценности побед в боевых действиях требуется определить, какие битвы, несмотря на успех, были наиболее «дорогими» в терминах потерь среди солдат и затрат ресурсов. Для каждой битвы необходимо рассчитать общее количество безвозвратных потерь (солдаты со статусом «убит» или «пропал без вести»), участвовавших в ней, а также среднюю исходную боевую эффективность подразделений, принимавших в ней участие. Дополнительно нужно подсчитать количество единиц снаряжения, выданного солдатам, участвовавшим в битве. На основе этих данных вычислите условный стоимостной коэффициент битвы (cost_ratio) как отношение числа потерь к средней боевой эффективности, округленное до 2 знаков. Затем проранжируйте все битвы по убыванию числа потерь (loss_rank) и по убыванию средней эффективности (eff_rank) через DENSE_RANK(). Отсортируйте итоговый список по убыванию cost_ratio, затем по названию битвы.

Формат результата (столбцы строго в указанном порядке):
1. battle_name — название битвы (сражения);
2. losses — общее количество безвозвратных потерь личного состава;
3. avg_efficiency — средняя исходная боевая эффективность задействованных подразделений;
4. equipment_used — суммарный объем использованного снаряжения;
5. loss_rank — ранг битвы по числу потерь через DENSE_RANK() (1 — наибольшие потери);
6. eff_rank — ранг битвы по средней эффективности через DENSE_RANK() (1 — наибольшая эффективность);
7. cost_ratio — стоимостной коэффициент битвы (losses / avg_efficiency, округленный до 2 знаков).',
    clue = 'Используйте CTE для подсчёта потерь, средней эффективности ROUND(AVG(mu.combat_efficiency)::numeric, 1)::float и выданного снаряжения COALESCE(SUM(ea.quantity), 0)::int. В основном запросе рассчитайте DENSE_RANK() OVER (ORDER BY losses DESC) и DENSE_RANK() OVER (ORDER BY avg_efficiency DESC), а также ROUND((losses / NULLIF(avg_efficiency, 0))::numeric, 2)::float AS cost_ratio.',
    correct_query = 'WITH battle_stats AS (
    SELECT b.id AS battle_id,
           b.battle_name,
           COUNT(DISTINCT s.id) FILTER (WHERE s.status IN (''убит'', ''пропал без вести''))::int AS losses,
           ROUND(AVG(mu.combat_efficiency)::numeric, 1)::float AS avg_efficiency,
           COALESCE(SUM(ea.quantity), 0)::int AS equipment_used
    FROM battle b
    JOIN battle_military_unit bmu ON b.id = bmu.battle_id
    JOIN military_unit mu ON bmu.unit_id = mu.id
    LEFT JOIN military_service ms ON mu.id = ms.unit_id
         AND ms.start_date <= b.end_date AND (ms.end_date IS NULL OR ms.end_date >= b.start_date)
    LEFT JOIN soldier s ON ms.soldier_id = s.id
    LEFT JOIN equipment_assignment ea ON s.id = ea.soldier_id
    GROUP BY b.id, b.battle_name
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
    expected_result = '{"columns": ["battle_name", "losses", "avg_efficiency", "equipment_used", "loss_rank", "eff_rank", "cost_ratio"], "data": [["Сталинградская битва", 2, 92.5, 6, 1, 9, 0.02], ["Балатонская операция", 1, 97.6, 1, 2, 3, 0.01], ["Битва за Воронеж", 1, 92.3, 6, 2, 10, 0.01], ["Битва за Днепр", 1, 94.4, 0, 2, 7, 0.01], ["Битва за Кавказ", 1, 96.7, 0, 2, 4, 0.01], ["Битва при Дебрецене", 1, 96.7, 0, 2, 4, 0.01], ["Блокада Ленинграда", 1, 76.6, 0, 2, 22, 0.01], ["Будапештская операция", 1, 96.7, 0, 2, 4, 0.01], ["Восточно-Прусская операция", 1, 87.2, 24, 2, 15, 0.01], ["Корсунь-Шевченковская операция", 1, 89.5, 2, 2, 12, 0.01], ["Ржевская битва", 1, 83.3, 121, 2, 17, 0.01], ["Харьковская операция", 1, 81.8, 0, 2, 19, 0.01], ["Берлинская операция", 0, 98.5, 1, 3, 1, 0.0], ["Битва за Берлин", 0, 98.2, 121, 3, 2, 0.0], ["Битва за Москву", 0, 87.2, 121, 3, 15, 0.0], ["Висло-Одерская операция", 0, 96.4, 120, 3, 5, 0.0], ["Демянская операция", 0, 78.0, 1, 3, 21, 0.0], ["Керченско-Эльтигенская операция", 0, 88.9, 0, 3, 13, 0.0], ["Курская битва", 0, 87.9, 4, 3, 14, 0.0], ["Маньчжурская операция", 0, 68.3, 0, 3, 25, 0.0], ["Оборона Брестской крепости", 0, 96.2, 0, 3, 6, 0.0], ["Оборона Брестской крепости", 0, 96.2, 0, 3, 6, 0.0], ["Оборона Заполярья", 0, 73.9, 0, 3, 24, 0.0], ["Оборона Севастополя", 0, 82.4, 0, 3, 18, 0.0], ["Оборона Тулы", 0, 85.2, 0, 3, 16, 0.0], ["Операция \"Багратион\"", 0, 92.8, 2, 3, 8, 0.0], ["Пражская операция", 0, 90.0, 0, 3, 11, 0.0], ["Прорыв блокады Ленинграда", 0, 75.2, 1, 3, 23, 0.0], ["Смоленское сражение", 0, 80.3, 121, 3, 20, 0.0], ["Таллинский переход", 0, 96.2, 0, 3, 6, 0.0]], "row_count": 30}'::jsonb
WHERE task_global_id = 62;
