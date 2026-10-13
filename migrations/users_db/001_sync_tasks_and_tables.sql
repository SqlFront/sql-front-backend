-- Migration 001: Sync tasks and ensure tables
-- 1. Ensure quest_tasks_solved table exists
CREATE TABLE IF NOT EXISTS public.quest_tasks_solved (
    id SERIAL PRIMARY KEY,
    user_id integer NOT NULL REFERENCES public.users(user_id),
    quest_id character varying NOT NULL,
    scene_id character varying NOT NULL,
    user_query text,
    created_at timestamp with time zone DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_quest_tasks_solved_user_id ON public.quest_tasks_solved(user_id);
CREATE INDEX IF NOT EXISTS idx_quest_tasks_solved_quest_scene ON public.quest_tasks_solved(quest_id, scene_id);

-- 2. Sync all 97 tasks (including fixes and new missions)
INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (1, 0, 1, 'Архив личного состава', 'Составьте список всех военнослужащих с указанием их полных имен и годов рождения. Это необходимо для анализа возрастного состава армии и планирования ресурсов', 'Используйте таблицу `soldier`, выбрав два ключевых столбца.', NULL, '{"data": [["Иванов Алексей Петрович", 1923], ["Смирнова Анна Васильевна", 1925], ["Петров Дмитрий Иванович", 1918], ["Козлов Николай Семёнович", 1920], ["Фёдорова Мария Ивановна", 1922], ["Жуков Андрей Григорьевич", 1915], ["Павлов Яков Фёдорович", 1917], ["Зайцева Людмила Михайловна", 1924], ["Громов Михаил Сергеевич", 1919], ["Орлова Вера Павловна", 1921], ["Новиков Александр Иванович", 1924], ["Васнецова Татьяна Дмитриевна", 1923], ["Кузнецов Пётр Васильевич", 1916], ["Белов Алексей Николаевич", 1925], ["Соколова Ольга Ивановна", 1920], ["Морозов Иван Кузьмич", 1914], ["Волкова Елена Сергеевна", 1926], ["Ткаченко Григорий Петрович", 1927], ["Беляев Павел Дмитриевич", 1912], ["Семёнова Валентина Михайловна", 1920], ["Ковалёв Сергей Николаевич", 1925], ["Мельникова Галина Ивановна", 1924], ["Фёдоров Игорь Васильевич", 1913], ["Горбачёв Алексей Дмитриевич", 1926], ["Сидорова Екатерина Петровна", 1921], ["Смирнов Василий Иванович", 1911], ["Крылова Надежда Фёдоровна", 1925], ["Орлов Денис Сергеевич", 1927], ["Жукова Елена Викторовна", 1923], ["Гришин Алексей Петрович", 1918], ["Ткаченко Иван Григорьевич", 1920], ["Воронцова Лидия Павловна", 1924], ["Жуковский Виктор Михайлович", 1915], ["Морозова Анна Сергеевна", 1922], ["Кузнецов Артём Игоревич", 1926], ["Соколовская Надежда Викторовна", 1923], ["Белов Дмитрий Николаевич", 1917], ["Громова Екатерина Ивановна", 1925], ["Фролов Павел Сергеевич", 1928], ["Ковалёва Ольга Дмитриевна", 1921]], "columns": ["full_name", "birth_year"], "row_count": 40}', '{first_any_level,supply,easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (2, 0, 2, 'География сражений', 'Определите все боевые операции, проведенные в Сталинграде. Результаты помогут оценить стратегическую значимость этого региона', 'Фильтрация по локации в таблице `battles` с использованием точного значения', NULL, '{"data": [["Сталинградская битва"]], "columns": ["battle_name"], "row_count": 1}', '{stalingrad,easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (4, 0, 3, 'Оптимизация численности', 'Найдите количество подразделений, где численность личного состава людей не превышает 500 человек. Вычисленный столбец назовите answer. Это критично для перераспределения сил между частями', 'Используйте вложенный запрос с группировкой и агрегатной функцией для подсчета солдат', NULL, '{"data": [[29]], "columns": ["answer"], "row_count": 1}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (5, 0, 4, 'Хроники войны', 'Выведите список всех сражений с их названиями, датами начала и окончания и местоположениями, отсортированный в хронологическом порядке по дате начала. Это ключ к пониманию этапов войны. Примечание: в результате допустимо дублирование данных.', 'Сортировка по дате в таблице `battle` с указанием направления', NULL, '{"data": [["Оборона Брестской крепости", "1941-06-22", "1941-06-29", "Брест"], ["Оборона Брестской крепости", "1941-06-22", "1941-06-29", "Брест"], ["Оборона Заполярья", "1941-06-29", "1944-10-01", "Мурманск"], ["Смоленское сражение", "1941-07-10", "1941-09-10", "Смоленск"], ["Таллинский переход", "1941-08-27", "1941-08-30", "Балтийское море"], ["Блокада Ленинграда", "1941-09-08", "1944-01-27", "Ленинград"], ["Битва за Москву", "1941-09-30", "1942-04-20", "Москва"], ["Оборона Тулы", "1941-10-24", "1941-12-05", "Тула"], ["Оборона Севастополя", "1941-10-30", "1942-07-04", "Севастополь"], ["Ржевская битва", "1942-01-08", "1943-03-31", "Ржев"], ["Демянская операция", "1942-02-20", "1942-05-20", "Новгородская обл."], ["Харьковская операция", "1942-05-12", "1942-05-28", "Харьков"], ["Битва за Воронеж", "1942-06-28", "1943-01-25", "Воронеж"], ["Сталинградская битва", "1942-07-17", "1943-02-02", "Сталинград"], ["Битва за Кавказ", "1942-07-25", "1943-10-09", "Кавказ"], ["Прорыв блокады Ленинграда", "1943-01-12", "1943-01-30", "Ленинград"], ["Курская битва", "1943-07-05", "1943-08-23", "Курск"], ["Битва за Днепр", "1943-08-26", "1943-12-23", "Днепр"], ["Керченско-Эльтигенская операция", "1943-10-31", "1943-12-11", "Керчь"], ["Корсунь-Шевченковская операция", "1944-01-24", "1944-02-17", "Украина"], ["Операция \"Багратион\"", "1944-06-23", "1944-08-29", "Белоруссия"], ["Битва при Дебрецене", "1944-10-06", "1944-10-29", "Венгрия"], ["Будапештская операция", "1944-10-29", "1945-02-13", "Венгрия"], ["Висло-Одерская операция", "1945-01-12", "1945-02-03", "Польша"], ["Восточно-Прусская операция", "1945-01-13", "1945-04-25", "Кёнигсберг"], ["Балатонская операция", "1945-03-06", "1945-03-15", "Венгрия"], ["Берлинская операция", "1945-04-16", "1945-05-08", "Берлин"], ["Битва за Берлин", "1945-04-16", "1945-05-08", "Берлин"], ["Пражская операция", "1945-05-06", "1945-05-11", "Прага"], ["Маньчжурская операция", "1945-08-09", "1945-09-02", "Маньчжурия"]], "columns": ["battle_name", "start_date", "end_date", "location"], "row_count": 30}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (6, 0, 5, 'Галерея героев', 'Создайте список солдат и наград, которые они получили. Это основа для формирования мемориальных архивов', 'Объединение трех таблиц: `soldier`, `soldier_medal` и `medal` через INNER JOIN', NULL, '{"data": [["Павлов Яков Фёдорович", "Герой Советского Союза"], ["Зайцева Людмила Михайловна", "Медаль \"За отвагу\""], ["Жуков Андрей Григорьевич", "Орден Красной Звезды"], ["Громов Михаил Сергеевич", "Орден Отечественной войны"], ["Орлова Вера Павловна", "Орден Славы"], ["Новиков Александр Иванович", "Орден Красной Звезды"], ["Васнецова Татьяна Дмитриевна", "Медаль \"Партизану Отечественной войны\""], ["Кузнецов Пётр Васильевич", "Герой Советского Союза"], ["Белов Алексей Николаевич", "Медаль \"За оборону Сталинграда\""], ["Соколова Ольга Ивановна", "Медаль \"За оборону Москвы\""], ["Иванов Алексей Петрович", "Медаль \"За отвагу\""], ["Смирнова Анна Васильевна", "Орден Отечественной войны"], ["Петров Дмитрий Иванович", "Медаль \"За взятие Берлина\""]], "columns": ["full_name", "medal_name"], "row_count": 13}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (7, 0, 6, 'Семейная история', 'Выявите всех солдат с фамилией, начинающейся на «Иванов». Возможно, это представители одной семьи', 'Используйте оператор `LIKE` с шаблоном для поиска по началу строки', NULL, '{"data": [["Иванов Алексей Петрович"]], "columns": ["full_name"], "row_count": 1}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (8, 0, 7, 'Элитные подразделения', 'Найдите все воинские части(подразделения), в названии которых встречается слово «гвардейская» (в любом регистре). Такие части часто были элитой армии', 'Регистронезависимый поиск через `ILIKE`', NULL, '{"data": [["1-я гвардейская танковая армия"], ["7-я гвардейская миномётная дивизия"], ["8-я гвардейская армия"]], "columns": ["unit_name"], "row_count": 3}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (9, 0, 8, 'Артиллерийский учет', 'Составьте список снаряжения, в названии которого есть «пушка». Это поможет оценить наличие тяжелого вооружения', 'Используйте POSIX-оператор `~` для поиска по регулярному выражению', 'SELECT item_name FROM equipment WHERE item_name ~ ''пушка'';', '{"data": [["76-мм дивизионная пушка ЗИС-3"]], "columns": ["item_name"], "row_count": 1}', '{easy,supply}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (10, 0, 9, 'Отцовские корни', 'Найдите солдат с отчеством «Петрович» или «Иванович». Данные могут быть полезны для генеалогических исследований', 'Примените POSIX-оператор `|` для выбора одного из двух вариантов', 'SELECT full_name FROM soldier WHERE full_name ~ ''(Петрович|Иванович)$'';', '{"data": [["Иванов Алексей Петрович"], ["Петров Дмитрий Иванович"], ["Новиков Александр Иванович"], ["Ткаченко Григорий Петрович"], ["Смирнов Василий Иванович"], ["Гришин Алексей Петрович"]], "columns": ["full_name"], "row_count": 6}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (11, 0, 10, 'Исключение стрелковых частей', 'Выведите названия подразделений, не относящихся к стрелковым. Это важно для анализа структуры войск', 'Используйте `NOT LIKE` для исключения определенного типа частей', 'SELECT unit_name FROM military_unit WHERE unit_type NOT LIKE ''%танковая%'';', '{"data": [["62-я армия"], ["1-я гвардейская танковая армия"], ["16-я воздушная армия"], ["7-я гвардейская миномётная дивизия"], ["2-я ударная армия"], ["8-я гвардейская армия"], ["3-я воздушная армия"], ["14-я отдельная штрафная рота"], ["1-я морская бригада"], ["Отдельная медико-санитарная рота"], ["88-й отдельный лыжный батальон"], ["101-й полк НКВД"], ["369-й отдельный батальон морской пехоты"], ["1-й чехословацкий отдельный батальон"], ["585-й женский авиаполк"], ["28-я дивизия народного ополчения"], ["Отдельный отряд собак-истребителей танков"], ["37-й гвардейский миномётный полк"], ["Отдельный батальон связи №45"], ["225-й отдельный инженерный батальон"], ["18-я дивизия СС \"Хорст Вессель\""], ["101-й учебный полк"], ["1-й отдельный чехословацкий батальон"], ["46-й гвардейский ночной бомбардировочный полк"], ["101-й инженерно-сапёрный батальон"], ["Отдельный отряд собак-миноискателей"]], "columns": ["unit_name"], "row_count": 26}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (13, 0, 12, 'Тип операции', 'Выявите бои, в названии которых есть слова «освобождение» или «оборона». Это поможет классифицировать сражения по их целям', 'Примените POSIX-оператор `|` для поиска по двум ключевым словам', 'SELECT battle_name FROM battle WHERE battle_name ~ ''(Освобождение|Оборона)'';', '{"data": [["Оборона Брестской крепости"], ["Оборона Севастополя"], ["Оборона Заполярья"], ["Оборона Брестской крепости"], ["Оборона Тулы"]], "columns": ["battle_name"], "row_count": 5}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (12, 0, 11, 'Короткие названия', 'Найдите снаряжение, название которого состоит ровно из 4 символов. Возможно, это кодированные обозначения', 'Используйте `LIKE` с пятью символами `_`', NULL, '{"data": [["Т-34"], ["Ил-2"], ["М-31"], ["ИС-2"], ["ПТРД"]], "columns": ["item_name"], "row_count": 5}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (15, 0, 14, 'Средний возраст победителей', 'Рассчитайте средний возраст солдат на момент окончания войны (1945 год). Назовите столбец average_age. Это ключевой показатель для демографического анализа', 'Используйте арифметические операции с `AVG` и `birth_year`', NULL, '{"data": [[23.875]], "columns": ["average_age"], "row_count": 1}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (41, 1, 9, 'Логистика Сталинградского фронта', 'Рассчитайте объем снаряжения на одного солдата в Сталинграде за период обороны. Это покажет, насколько войска были обеспечены ресурсами', 'Используйте `ROUND` и арифметические операции с группировкой по типам снаряжения', NULL, '{"data": [["артиллерия", 72, "24.00"]], "columns": ["equipment_type", "total", "per_soldier"], "row_count": 1}', '{supply,stalingrad,medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (3, 0, 15, 'Логистика вооружений', 'Определите общее количество снаряжения каждого типа. Назовите вычисленное поле "total". Это основа для оценки обеспеченности войск', 'Группировка по типу снаряжения с применением `SUM`', NULL, '{"data": [["авиабомбы", 3200], ["боеприпасы", 310000], ["артиллерия", 24], ["миномёты", 2268], ["противотанковые", 68], ["связь", 15], ["медицина", 1330], ["самолёты", 45], ["инженерное", 850], ["реактивные снаряды", 1500], ["оружие", 1200], ["танки", 100]], "columns": ["equipment_type", "total"], "row_count": 12}', '{window,easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (16, 0, 16, 'История формирования', 'Найдите самую раннюю и позднюю даты создания воинских частей. Это отразит этапы развития армии', 'Используйте агрегатные функции `MIN` и `MAX` для дат', NULL, '{"data": [["1939-04-20", "1944-01-10"]], "columns": ["min", "max"], "row_count": 1}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (17, 0, 17, 'Идентификация званий', 'Создайте строку, объединяющую имя солдата и его звание в формате "ФИО (звание)". Назовите получившееся поле soldier_info. Это упростит работу с архивными записями', 'Конкатенация строк с использованием `||`', NULL, '{"data": [["Иванов Алексей Петрович (рядовой)"], ["Смирнова Анна Васильевна (медсестра)"], ["Петров Дмитрий Иванович (сержант)"], ["Козлов Николай Семёнович (лейтенант)"], ["Фёдорова Мария Ивановна (санитар)"], ["Жуков Андрей Григорьевич (капитан)"], ["Павлов Яков Фёдорович (сержант)"], ["Зайцева Людмила Михайловна (снайпер)"], ["Громов Михаил Сергеевич (старшина)"], ["Орлова Вера Павловна (радист)"], ["Новиков Александр Иванович (ефрейтор)"], ["Васнецова Татьяна Дмитриевна (разведчик)"], ["Кузнецов Пётр Васильевич (майор)"], ["Белов Алексей Николаевич (рядовой)"], ["Соколова Ольга Ивановна (хирург)"], ["Морозов Иван Кузьмич (полковник)"], ["Волкова Елена Сергеевна (зенитчик)"], ["Ткаченко Григорий Петрович (рядовой)"], ["Беляев Павел Дмитриевич (подполковник)"], ["Семёнова Валентина Михайловна (связист)"], ["Ковалёв Сергей Николаевич (лейтенант)"], ["Мельникова Галина Ивановна (снайпер)"], ["Фёдоров Игорь Васильевич (полковник)"], ["Горбачёв Алексей Дмитриевич (рядовой)"], ["Сидорова Екатерина Петровна (радист)"], ["Смирнов Василий Иванович (генерал-майор)"], ["Крылова Надежда Фёдоровна (санитар)"], ["Орлов Денис Сергеевич (рядовой)"], ["Жукова Елена Викторовна (радист)"], ["Гришин Алексей Петрович (капитан)"], ["Ткаченко Иван Григорьевич (старший сержант)"], ["Воронцова Лидия Павловна (снайпер)"], ["Жуковский Виктор Михайлович (полковник)"], ["Морозова Анна Сергеевна (радист)"], ["Кузнецов Артём Игоревич (рядовой)"], ["Соколовская Надежда Викторовна (хирург)"], ["Белов Дмитрий Николаевич (капитан)"], ["Громова Екатерина Ивановна (зенитчик)"], ["Фролов Павел Сергеевич (рядовой)"], ["Ковалёва Ольга Дмитриевна (разведчик)"]], "columns": ["soldier_info"], "row_count": 40}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (18, 0, 18, 'География призыва', 'Определите количество уникальных городов, откуда призывались солдаты. Это покажет масштаб мобилизации', 'Используйте `COUNT(DISTINCT ...)` для столбца с городами', NULL, '{"data": [[22]], "columns": ["count"], "row_count": 1}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (19, 0, 19, 'Эффективность подразделений', 'Рассчитайте среднюю боевую эффективность для каждого типа частей. Вычисленное значение назовите avg_efficiency. Результат выведите в алфавитном порядке. Это поможет оценить их вклад в победу', 'Группировка по `unit_type` с функцией `AVG`', NULL, '{"data": [["авиация", 91.175], ["инженерные войска", 89.6], ["лыжные войска", 73.9], ["медицинская", 91.7], ["морская пехота", 85.65], ["общевойсковая", 83.75], ["пехота", 83.0125], ["противник", 88.1], ["реактивная артиллерия", 93.5], ["резерв", 68.3], ["связисты", 85.2], ["спецназ", 86.63333333333334], ["танковые войска", 96.75]], "columns": ["unit_type", "avg_efficiency"], "row_count": 13}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (21, 0, 21, 'Анализ надежности', 'Вычислите дисперсию боевой эффективности для каждого типа частей. Назовите столбец variance и отсортируйте результат по алфавиту. Высокая дисперсия может указывать на нестабильность', 'Используйте `VAR_SAMP` для расчета дисперсии', NULL, '{"data": [["авиация", 27.4625], ["инженерные войска", 0.02], ["лыжные войска", null], ["медицинская", null], ["морская пехота", 21.125], ["общевойсковая", 146.205], ["пехота", 121.09553571428572], ["противник", null], ["реактивная артиллерия", 18.0], ["резерв", null], ["связисты", null], ["спецназ", 68.94333333333333], ["танковые войска", 6.125]], "columns": ["unit_type", "variance"], "row_count": 13}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (67, 1, 10, 'Снаряжение героев', 'Найдите солдат, получивших снаряжение 12 января 1943 года. Это может быть связано с подготовкой к операции «Искра»', 'Примените вложенные запросы и фильтрацию по дате и ID снаряжения', NULL, '{"data": [["Смирнова Анна Васильевна"]], "columns": ["full_name"], "row_count": 1}', '{medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (20, 0, 20, 'Статистика потерь', 'Подсчитайте количество солдат по каждому статусу (status). Это основа для анализа людских потерь', 'Группировка по статусу с использованием `CASE` в `COUNT`', NULL, '{"data": [["жив", 16], ["пропал без вести", 7], ["ранен", 8], ["убит", 9]], "columns": ["status", "count"], "row_count": 4}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (22, 0, 22, 'Классификация эффективности', 'Разделите части на три категории: высокая, средняя и низкая эффективность. Столбец с категориями назовите efficiency_category. Это основа для стратегического планирования. Примечание: "Высокая" (КПД ≥ 90), "Средняя" (70 ≤ КПД < 90), "Низкая" (КПД < 70).', 'Примените `CASE` с диапазонами значений `combat_efficiency`', NULL, '{"data": [["316-я стрелковая дивизия", "Средняя"], ["62-я армия", "Высокая"], ["1-я гвардейская танковая армия", "Высокая"], ["150-я стрелковая дивизия", "Высокая"], ["16-я воздушная армия", "Средняя"], ["7-я гвардейская миномётная дивизия", "Высокая"], ["2-я ударная армия", "Средняя"], ["8-я гвардейская армия", "Высокая"], ["3-я воздушная армия", "Средняя"], ["106-я стрелковая дивизия", "Средняя"], ["14-я отдельная штрафная рота", "Низкая"], ["1-я морская бригада", "Средняя"], ["Отдельная медико-санитарная рота", "Высокая"], ["88-й отдельный лыжный батальон", "Средняя"], ["101-й полк НКВД", "Высокая"], ["369-й отдельный батальон морской пехоты", "Средняя"], ["1-й чехословацкий отдельный батальон", "Средняя"], ["585-й женский авиаполк", "Высокая"], ["28-я дивизия народного ополчения", "Низкая"], ["Отдельный отряд собак-истребителей танков", "Средняя"], ["37-й гвардейский миномётный полк", "Высокая"], ["Отдельный батальон связи №45", "Средняя"], ["225-й отдельный инженерный батальон", "Средняя"], ["18-я дивизия СС \"Хорст Вессель\"", "Средняя"], ["101-й учебный полк", "Низкая"], ["64-я стрелковая дивизия", "Высокая"], ["1-й отдельный чехословацкий батальон", "Средняя"], ["46-й гвардейский ночной бомбардировочный полк", "Высокая"], ["101-й инженерно-сапёрный батальон", "Средняя"], ["Отдельный отряд собак-миноискателей", "Средняя"]], "columns": ["unit_name", "efficiency_category"], "row_count": 30}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (69, 1, 11, 'Возрастные категории', 'Посчитайте сколько солдат в каждой возрастной группе на момент начала войны(< 18, 18-25, > 25). Колонку с группой назовите age_group, а с количеством солдат — quantity. Результат отсортируйте по убыванию количества. Это поможет понять, какие возрастные группы преобладали в армии', 'Используйте `CASE` с диапазонами на основе года рождения', NULL, '{"data": [["18-25", 19], ["< 18", 15], ["> 25", 6]], "columns": ["age_group", "quantity"], "row_count": 3}', '{medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (27, 0, 27, 'Долгие сражения', 'Найдите бои, длившиеся более 30 дней. Вычисленный столбец назовите duration_days. Результат отсортируйте по убыванию длительности. Такие операции часто становились переломными', 'Рассчитайте разницу между датами начала и окончания с использованием `HAVING`', NULL, '{"data": [["Оборона Заполярья", 1190], ["Блокада Ленинграда", 871], ["Ржевская битва", 447], ["Битва за Кавказ", 441], ["Оборона Севастополя", 247], ["Битва за Воронеж", 211], ["Битва за Москву", 202], ["Сталинградская битва", 200], ["Битва за Днепр", 119], ["Будапештская операция", 107], ["Восточно-Прусская операция", 102], ["Демянская операция", 89], ["Операция \"Багратион\"", 67], ["Смоленское сражение", 62], ["Курская битва", 49], ["Оборона Тулы", 42], ["Керченско-Эльтигенская операция", 41]], "columns": ["battle_name", "duration_days"], "row_count": 17}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (29, 0, 29, 'Молодая кровь', 'Для каждой части определите самого молодого солдата. Выведите название части и год рождения самого молодого солдата. Назовите вычисленный столбец youngest_birth_year, а результат отсортируйте по убыванию годов рождения. Это может указывать на пополнение в критический момент', 'Используйте `MAX` с годом рождения и группировку по частям', NULL, '{"data": [["101-й инженерно-сапёрный батальон", 1928], ["Отдельная медико-санитарная рота", 1927], ["225-й отдельный инженерный батальон", 1927], ["1-я морская бригада", 1926], ["Отдельный отряд собак-миноискателей", 1926], ["28-я дивизия народного ополчения", 1926], ["Отдельный батальон связи №45", 1925], ["369-й отдельный батальон морской пехоты", 1925], ["62-я армия", 1925], ["46-й гвардейский ночной бомбардировочный полк", 1925], ["150-я стрелковая дивизия", 1925], ["1-й чехословацкий отдельный батальон", 1924], ["3-я воздушная армия", 1924], ["1-й отдельный чехословацкий батальон", 1924], ["18-я дивизия СС \"Хорст Вессель\"", 1923], ["64-я стрелковая дивизия", 1923], ["316-я стрелковая дивизия", 1923], ["106-я стрелковая дивизия", 1923], ["8-я гвардейская армия", 1921], ["Отдельный отряд собак-истребителей танков", 1921], ["101-й полк НКВД", 1920], ["16-я воздушная армия", 1920], ["1-я гвардейская танковая армия", 1920], ["2-я ударная армия", 1919], ["101-й учебный полк", 1918], ["14-я отдельная штрафная рота", 1914], ["585-й женский авиаполк", 1913], ["88-й отдельный лыжный батальон", 1912], ["37-й гвардейский миномётный полк", 1911]], "columns": ["unit_name", "youngest_birth_year"], "row_count": 29}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (30, 0, 30, 'Танковые части', 'Найдите подразделения, оснащенные танками. Это важно для анализа бронетанковых сил', 'Используйте подзапрос с `EXISTS` для проверки наличия снаряжения', NULL, '{"data": [["1-я гвардейская танковая армия"], ["8-я гвардейская армия"]], "columns": ["unit_name"], "row_count": 2}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (31, 0, 31, 'Ветераны частей', 'Определите солдат, которые были старше всех в своем подразделении. Возможно, это опытные командиры', 'Примените подзапрос с `ALL` для сравнения возрастов', NULL, '{"data": [["Фёдорова Мария Ивановна"], ["Жуков Андрей Григорьевич"], ["Павлов Яков Фёдорович"], ["Зайцева Людмила Михайловна"], ["Громов Михаил Сергеевич"], ["Орлова Вера Павловна"], ["Новиков Александр Иванович"], ["Васнецова Татьяна Дмитриевна"], ["Кузнецов Пётр Васильевич"], ["Морозов Иван Кузьмич"], ["Волкова Елена Сергеевна"], ["Ткаченко Григорий Петрович"], ["Беляев Павел Дмитриевич"], ["Семёнова Валентина Михайловна"], ["Ковалёв Сергей Николаевич"], ["Мельникова Галина Ивановна"], ["Фёдоров Игорь Васильевич"], ["Горбачёв Алексей Дмитриевич"], ["Сидорова Екатерина Петровна"], ["Смирнов Василий Иванович"], ["Крылова Надежда Фёдоровна"], ["Орлов Денис Сергеевич"], ["Жукова Елена Викторовна"], ["Гришин Алексей Петрович"], ["Ткаченко Иван Григорьевич"], ["Жуковский Виктор Михайлович"], ["Морозова Анна Сергеевна"], ["Белов Дмитрий Николаевич"], ["Ковалёва Ольга Дмитриевна"]], "columns": ["full_name"], "row_count": 29}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (34, 0, 32, 'Неуничтоженные враги', 'Определите вражеские части, которые не были ликвидированы. Отсортируйте результат по убыванию. Это может указывать на сохранившиеся угрозы', 'Используйте `EXCEPT` для исключения уничтоженных частей', NULL, '{"data": [["Эскадра JG54 \"Зелёное сердце\""], ["Люфтваффе: эскадра JG52"]], "columns": ["unit_name"], "row_count": 2}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (37, 1, 1, 'Логистика Сталинградской битвы', 'Определите общее количество боеприпасов, выделенных каждой части в Сталинграде. Выведите уникальный идентификатор части, а вычисленный столбец назовите total_ammo. Это поможет оценить обеспеченность войск в критический период обороны', 'Используйте оконную функцию `SUM` с группировкой по `unit_id` и подзапрос для фильтрации локации', NULL, '{"data": [[2, 50000], [13, 30000], [18, 40000], [21, 50000], [26, 70000]], "columns": ["unit_id", "total_ammo"], "row_count": 5}', '{first_any_level,supply,window,stalingrad,medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (63, 1, 2, 'Снабжение перед операцией', 'Для воинских частей, у которых общее количество всего снаряжения на складе превышает 1000 единиц, необходимо вывести название части, а также суммарное количество находящихся в ней боеприпасов ammunition_total и медикаментов medicine_total. Это важно для планирования крупных наступлений', 'Сначала найдите подразделения, где общее количество снаряжения больше 1000, используя GROUP BY и HAVING SUM(quantity). Затем, для этих подразделений, посчитайте суммы по типам, применив условную агрегацию в основном запросе', NULL, '{"data": [["1-я морская бригада", 0, 250], ["3-я воздушная армия", 0, 0], ["316-я стрелковая дивизия", 50000, 0], ["37-й гвардейский миномётный полк", 50000, 0], ["585-й женский авиаполк", 40000, 0], ["62-я армия", 50000, 830], ["64-я стрелковая дивизия", 70000, 0], ["7-я гвардейская миномётная дивизия", 20000, 0], ["Отдельная медико-санитарная рота", 30000, 250]], "columns": ["unit_name", "ammunition_total", "medicine_total"], "row_count": 9}', '{cte,medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (38, 1, 3, 'Поиск героев для награждения', 'Выявите 20 солдат, участвовавших в наибольшем количестве сражений, и присвойте им ранги. Вычисленные столбцы назовите battles_participated и hero_rank. Это основа для награждения орденами и медалями', 'Используйте `RANK()` с сортировкой по убыванию количества битв', NULL, '{"data": [["Жуков Андрей Григорьевич", 30, 1], ["Иванов Алексей Петрович", 28, 2], ["Громов Михаил Сергеевич", 23, 3], ["Жуковский Виктор Михайлович", 23, 3], ["Гришин Алексей Петрович", 21, 5], ["Семёнова Валентина Михайловна", 20, 6], ["Соколова Ольга Ивановна", 20, 6], ["Кузнецов Пётр Васильевич", 19, 8], ["Зайцева Людмила Михайловна", 17, 9], ["Орлова Вера Павловна", 17, 9], ["Фёдоров Игорь Васильевич", 16, 11], ["Кузнецов Артём Игоревич", 16, 11], ["Крылова Надежда Фёдоровна", 16, 11], ["Козлов Николай Семёнович", 16, 11], ["Фёдорова Мария Ивановна", 15, 15], ["Смирнов Василий Иванович", 15, 15], ["Соколовская Надежда Викторовна", 15, 15], ["Ковалёва Ольга Дмитриевна", 14, 18], ["Ткаченко Иван Григорьевич", 14, 18], ["Громова Екатерина Ивановна", 13, 20]], "columns": ["full_name", "battles_participated", "hero_rank"], "row_count": 20}', '{window,medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (39, 1, 4, 'Анализ эффективности частей', 'Выведите для каждого военного подразделения его исходную и скорректированную боевую эффективность. Корректировка рассчитывается путем уменьшения исходного показателя (combat_efficiency) пропорционально доле безвозвратных потерь (статусы «убит» и «пропал без вести») от общей численности личного состава в данном подразделении. Результат должен содержать: название подразделения, исходную боевую эффективность initial_efficiency, процент потерь loss_percentage, скорректированную боевую эффективность adjusted_efficiency. Это покажет, как потери влияют на боеспособность', 'Сгруппируйте солдат по подразделениям (unit_id). Внутри каждой группы посчитайте общую численность и количество безвозвратных потерь, используя условную агрегацию (CASE). Затем соедините результат с таблицей military_unit и примените формулу для расчета скорректированной эффективности.', NULL, '{"data": [["8-я гвардейская армия", 98.5, 0.0, 98.5], ["150-я стрелковая дивизия", 97.8, 0.0, 97.8], ["46-й гвардейский ночной бомбардировочный полк", 96.7, 0.0, 96.7], ["37-й гвардейский миномётный полк", 96.5, 0.0, 96.5], ["101-й полк НКВД", 96.2, 0.0, 96.2], ["1-я гвардейская танковая армия", 95.0, 0.0, 95.0], ["585-й женский авиаполк", 94.1, 0.0, 94.1], ["64-я стрелковая дивизия", 92.4, 0.0, 92.4], ["62-я армия", 92.3, 0.0, 92.3], ["Отдельная медико-санитарная рота", 91.7, 0.0, 91.7], ["225-й отдельный инженерный батальон", 89.7, 0.0, 89.7], ["101-й инженерно-сапёрный батальон", 89.5, 0.0, 89.5], ["106-я стрелковая дивизия", 89.3, 0.0, 89.3], ["16-я воздушная армия", 88.9, 0.0, 88.9], ["369-й отдельный батальон морской пехоты", 88.9, 0.0, 88.9], ["18-я дивизия СС \"Хорст Вессель\"", 88.1, 0.0, 88.1], ["316-я стрелковая дивизия", 85.5, 0.0, 85.5], ["Отдельный батальон связи №45", 85.2, 0.0, 85.2], ["3-я воздушная армия", 85.0, 0.0, 85.0], ["1-й отдельный чехословацкий батальон", 85.0, 0.0, 85.0], ["Отдельный отряд собак-истребителей танков", 82.4, 0.0, 82.4], ["1-я морская бригада", 82.4, 0.0, 82.4], ["Отдельный отряд собак-миноискателей", 81.3, 0.0, 81.3], ["1-й чехословацкий отдельный батальон", 78.5, 0.0, 78.5], ["2-я ударная армия", 75.2, 0.0, 75.2], ["88-й отдельный лыжный батальон", 73.9, 0.0, 73.9], ["28-я дивизия народного ополчения", 69.8, 0.0, 69.8], ["101-й учебный полк", 68.3, 0.0, 68.3], ["14-я отдельная штрафная рота", 65.8, 0.0, 65.8]], "columns": ["unit_name", "initial_efficiency", "loss_percentage", "adjusted_efficiency"], "row_count": 29}', '{cte,medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (40, 1, 5, 'Логистика Курской дуги', 'Определите рейтинг частей в Курске по объему снабжения. Выведите столбцы unit_name, equipment_type, total, supply_rank. Это ключевые данные для анализа подготовки к крупнейшему танковому сражению', 'Используйте `RANK()` с группировкой по типам снаряжения', NULL, '{"data": [["16-я воздушная армия", "самолёты", 45, 1], ["1-я гвардейская танковая армия", "танки", 58, 2]], "columns": ["unit_name", "equipment_type", "total", "supply_rank"], "row_count": 2}', '{supply,window,medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (64, 1, 6, 'Снабжение морской пехоты', 'Проанализируйте снаряжение морских пехотинцев в Севастополе. Выведите столбцы equipment_type, total, items. Это необходимо для оценки их готовности к обороне прибрежных зон', 'Используйте `STRING_AGG` для объединения названий снаряжения и фильтрацию по типу части', NULL, '{"data": [["медицина", 250, "Аптечки полевые"], ["миномёты", 2256, "82-мм, 50-мм"]], "columns": ["equipment_type", "total", "items"], "row_count": 2}', '{medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (75, 1, 7, 'Первый и последний', 'Определите первого и последнего солдата, вступившего в каждую часть. Выведите название части, ФИО первого first_enlisted и последнего last_enlisted вступившего солдата. Это может указывать на "костяк" подразделения', 'Примените `FIRST_VALUE()` и `LAST_VALUE()` с оконными функциями', NULL, '{"data": [["316-я стрелковая дивизия", "Иванов Алексей Петрович", "Фёдорова Мария Ивановна"], ["62-я армия", "Петров Дмитрий Иванович", "Павлов Яков Фёдорович"], ["1-я гвардейская танковая армия", "Козлов Николай Семёнович", "Кузнецов Пётр Васильевич"], ["150-я стрелковая дивизия", "Зайцева Людмила Михайловна", "Белов Алексей Николаевич"], ["16-я воздушная армия", "Жуков Андрей Григорьевич", "Соколова Ольга Ивановна"], ["2-я ударная армия", "Громов Михаил Сергеевич", "Громов Михаил Сергеевич"], ["8-я гвардейская армия", "Орлова Вера Павловна", "Орлова Вера Павловна"], ["3-я воздушная армия", "Новиков Александр Иванович", "Новиков Александр Иванович"], ["106-я стрелковая дивизия", "Васнецова Татьяна Дмитриевна", "Васнецова Татьяна Дмитриевна"], ["14-я отдельная штрафная рота", "Морозов Иван Кузьмич", "Морозов Иван Кузьмич"], ["1-я морская бригада", "Волкова Елена Сергеевна", "Волкова Елена Сергеевна"], ["Отдельная медико-санитарная рота", "Ткаченко Григорий Петрович", "Ткаченко Григорий Петрович"], ["88-й отдельный лыжный батальон", "Беляев Павел Дмитриевич", "Беляев Павел Дмитриевич"], ["101-й полк НКВД", "Семёнова Валентина Михайловна", "Семёнова Валентина Михайловна"], ["369-й отдельный батальон морской пехоты", "Ковалёв Сергей Николаевич", "Ковалёв Сергей Николаевич"], ["1-й чехословацкий отдельный батальон", "Мельникова Галина Ивановна", "Мельникова Галина Ивановна"], ["585-й женский авиаполк", "Фёдоров Игорь Васильевич", "Фёдоров Игорь Васильевич"], ["28-я дивизия народного ополчения", "Горбачёв Алексей Дмитриевич", "Горбачёв Алексей Дмитриевич"], ["Отдельный отряд собак-истребителей танков", "Сидорова Екатерина Петровна", "Сидорова Екатерина Петровна"], ["37-й гвардейский миномётный полк", "Смирнов Василий Иванович", "Смирнов Василий Иванович"], ["Отдельный батальон связи №45", "Крылова Надежда Фёдоровна", "Крылова Надежда Фёдоровна"], ["225-й отдельный инженерный батальон", "Орлов Денис Сергеевич", "Орлов Денис Сергеевич"], ["18-я дивизия СС \"Хорст Вессель\"", "Жукова Елена Викторовна", "Жукова Елена Викторовна"], ["101-й учебный полк", "Гришин Алексей Петрович", "Гришин Алексей Петрович"], ["64-я стрелковая дивизия", "Ткаченко Иван Григорьевич", "Соколовская Надежда Викторовна"], ["1-й отдельный чехословацкий батальон", "Белов Дмитрий Николаевич", "Воронцова Лидия Павловна"], ["46-й гвардейский ночной бомбардировочный полк", "Жуковский Виктор Михайлович", "Громова Екатерина Ивановна"], ["101-й инженерно-сапёрный батальон", "Морозова Анна Сергеевна", "Фролов Павел Сергеевич"], ["Отдельный отряд собак-миноискателей", "Ковалёва Ольга Дмитриевна", "Кузнецов Артём Игоревич"]], "columns": ["unit_name", "first_enlisted", "last_enlisted"], "row_count": 29}', '{medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (77, 1, 8, 'Солдаты 1942 года', 'Выведите список солдат и их частей, где служба началась в 1942 году. Результат отсортируйте по первому столбцу. Это поможет анализировать мобилизацию в критический период', 'Используйте подзапросы для фильтрации дат и объединения таблиц', NULL, '{"data": [["Белов Дмитрий Николаевич", "1-й отдельный чехословацкий батальон"], ["Громов Михаил Сергеевич", "2-я ударная армия"], ["Жукова Елена Викторовна", "18-я дивизия СС \"Хорст Вессель\""], ["Жуковский Виктор Михайлович", "46-й гвардейский ночной бомбардировочный полк"], ["Ковалёва Ольга Дмитриевна", "Отдельный отряд собак-миноискателей"], ["Мельникова Галина Ивановна", "1-й чехословацкий отдельный батальон"], ["Морозова Анна Сергеевна", "101-й инженерно-сапёрный батальон"], ["Морозов Иван Кузьмич", "14-я отдельная штрафная рота"], ["Павлов Яков Фёдорович", "62-я армия"], ["Семёнова Валентина Михайловна", "101-й полк НКВД"], ["Смирнова Анна Васильевна", "62-я армия"], ["Соколова Ольга Ивановна", "16-я воздушная армия"], ["Фёдоров Игорь Васильевич", "585-й женский авиаполк"]], "columns": ["full_name", "unit_name"], "row_count": 13}', '{medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (76, 1, 12, 'Скользящие потери', 'Проанализируйте динамику потерь среди солдат в 1942 году, используя данные о дате призыва. Для каждого месяца 1942 года рассчитайте количество солдат, погибших к этому моменту, и постройте трёхмесячное скользящее среднее для сглаживания временного ряда. Выведите номер месяца (month), количество потерь (killed) и скользящее среднее (moving_avg). Это покажет динамику снижения боеспособности', 'Используйте `AVG()` с окном `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW`', NULL, '{"data": [[5.0, 1, 1.0]], "columns": ["month", "killed", "moving_avg"], "row_count": 1}', '{medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (54, 1, 14, 'Накопленные ресурсы', 'Определите накопительный итог поставок боеприпасов в 1942 году. Выведите название подразделения, дату последнего пополнения, а вычисленный столбец назовите cumulative_ammo. Это отразит рост запасов перед ключевыми операциями', 'Примените `SUM() OVER` с сортировкой по дате пополнения', NULL, '{"data": [["316-я стрелковая дивизия", "1942-03-05", 50000], ["62-я армия", "1942-03-05", 50000], ["7-я гвардейская миномётная дивизия", "1942-12-01", 20000], ["Отдельная медико-санитарная рота", "1942-03-05", 30000], ["585-й женский авиаполк", "1942-03-05", 40000], ["37-й гвардейский миномётный полк", "1942-03-05", 50000], ["64-я стрелковая дивизия", "1942-03-05", 70000]], "columns": ["unit_name", "last_replenishment", "cumulative_ammo"], "row_count": 7}', '{supply,window,medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (71, 1, 15, 'Боевые товарищи', 'Выявите пары солдат, призванных из одного города. Чтобы избежать дубликатов (А, Б) и (Б, А), добавьте условие `s1.id < s2.id` (где s1 и s2 - алиасы таблицы). Назовите столбцы soldier_name1, soldier_name2 и common_city. Отсортируйте результат по всем столбцам. Это может указывать на дружеские связи или совместную службу', 'Примените самосоединение таблицы `soldier` по городу призыва', NULL, '{"data": [["Белов Алексей Николаевич", "Фролов Павел Сергеевич", "Севастополь"], ["Васнецова Татьяна Дмитриевна", "Жукова Елена Викторовна", "Смоленск"], ["Васнецова Татьяна Дмитриевна", "Ковалёва Ольга Дмитриевна", "Смоленск"], ["Волкова Елена Сергеевна", "Громова Екатерина Ивановна", "Горький"], ["Гришин Алексей Петрович", "Ткаченко Иван Григорьевич", "Харьков"], ["Жуков Андрей Григорьевич", "Сидорова Екатерина Петровна", "Минск"], ["Жукова Елена Викторовна", "Ковалёва Ольга Дмитриевна", "Смоленск"], ["Зайцева Людмила Михайловна", "Воронцова Лидия Павловна", "Ленинград"], ["Иванов Алексей Петрович", "Соколовская Надежда Викторовна", "Москва"], ["Козлов Николай Семёнович", "Гришин Алексей Петрович", "Харьков"], ["Козлов Николай Семёнович", "Ткаченко Иван Григорьевич", "Харьков"], ["Крылова Надежда Фёдоровна", "Морозова Анна Сергеевна", "Одесса"], ["Мельникова Галина Ивановна", "Кузнецов Артём Игоревич", "Сталинград"], ["Орлова Вера Павловна", "Крылова Надежда Фёдоровна", "Одесса"], ["Орлова Вера Павловна", "Морозова Анна Сергеевна", "Одесса"], ["Петров Дмитрий Иванович", "Кузнецов Артём Игоревич", "Сталинград"], ["Петров Дмитрий Иванович", "Мельникова Галина Ивановна", "Сталинград"], ["Смирнов Василий Иванович", "Жуковский Виктор Михайлович", "Киев"], ["Смирнова Анна Васильевна", "Воронцова Лидия Павловна", "Ленинград"], ["Смирнова Анна Васильевна", "Зайцева Людмила Михайловна", "Ленинград"], ["Соколова Ольга Ивановна", "Жуковский Виктор Михайлович", "Киев"], ["Соколова Ольга Ивановна", "Смирнов Василий Иванович", "Киев"], ["Соколова Ольга Ивановна", "Ткаченко Григорий Петрович", "Киев"], ["Ткаченко Григорий Петрович", "Жуковский Виктор Михайлович", "Киев"], ["Ткаченко Григорий Петрович", "Смирнов Василий Иванович", "Киев"], ["Фёдорова Мария Ивановна", "Жуковский Виктор Михайлович", "Киев"], ["Фёдорова Мария Ивановна", "Смирнов Василий Иванович", "Киев"], ["Фёдорова Мария Ивановна", "Соколова Ольга Ивановна", "Киев"], ["Фёдорова Мария Ивановна", "Ткаченко Григорий Петрович", "Киев"]], "columns": ["soldier_name1", "soldier_name2", "common_city"], "row_count": 29}', '{medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (43, 1, 16, 'Гендерный баланс', 'Определите части, где количество мужчин и женщин неравно. Выведите название части military_unit_name и отсортируйте результат в обратном порядке. Это отразит гендерные особенности мобилизации', 'Используйте `SUM` с `CASE` для подсчета и фильтрацию через `HAVING`', NULL, '{"data": [["Отдельный отряд собак-истребителей танков"], ["Отдельный батальон связи №45"], ["Отдельная медико-санитарная рота"], ["8-я гвардейская армия"], ["88-й отдельный лыжный батальон"], ["62-я армия"], ["585-й женский авиаполк"], ["3-я воздушная армия"], ["37-й гвардейский миномётный полк"], ["369-й отдельный батальон морской пехоты"], ["2-я ударная армия"], ["28-я дивизия народного ополчения"], ["225-й отдельный инженерный батальон"], ["1-я морская бригада"], ["1-я гвардейская танковая армия"], ["1-й чехословацкий отдельный батальон"], ["18-я дивизия СС \"Хорст Вессель\""], ["14-я отдельная штрафная рота"], ["106-я стрелковая дивизия"], ["101-й учебный полк"], ["101-й полк НКВД"]], "columns": ["military_unit_name"], "row_count": 21}', '{window,medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (44, 1, 17, 'Участники Сталинграда', 'Найдите всех солдат, служивших в частях, участвовавших в Сталинградской битве. Это основа для создания мемориальных списков', 'Используйте вложенные запросы с `IN` для фильтрации по ID частей', NULL, '{"data": [["Иванов Алексей Петрович"], ["Смирнова Анна Васильевна"], ["Петров Дмитрий Иванович"], ["Козлов Николай Семёнович"], ["Фёдорова Мария Ивановна"], ["Жуков Андрей Григорьевич"], ["Павлов Яков Фёдорович"], ["Зайцева Людмила Михайловна"], ["Громов Михаил Сергеевич"], ["Орлова Вера Павловна"], ["Новиков Александр Иванович"], ["Васнецова Татьяна Дмитриевна"], ["Кузнецов Пётр Васильевич"], ["Белов Алексей Николаевич"], ["Соколова Ольга Ивановна"], ["Морозов Иван Кузьмич"], ["Волкова Елена Сергеевна"], ["Ткаченко Григорий Петрович"], ["Беляев Павел Дмитриевич"], ["Семёнова Валентина Михайловна"], ["Ковалёв Сергей Николаевич"], ["Мельникова Галина Ивановна"], ["Фёдоров Игорь Васильевич"], ["Горбачёв Алексей Дмитриевич"], ["Сидорова Екатерина Петровна"], ["Смирнов Василий Иванович"], ["Крылова Надежда Фёдоровна"], ["Орлов Денис Сергеевич"], ["Жукова Елена Викторовна"], ["Гришин Алексей Петрович"], ["Ткаченко Иван Григорьевич"], ["Воронцова Лидия Павловна"], ["Жуковский Виктор Михайлович"], ["Морозова Анна Сергеевна"], ["Кузнецов Артём Игоревич"], ["Соколовская Надежда Викторовна"], ["Белов Дмитрий Николаевич"], ["Громова Екатерина Ивановна"], ["Фролов Павел Сергеевич"], ["Ковалёва Ольга Дмитриевна"]], "columns": ["full_name"], "row_count": 40}', '{stalingrad,medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (72, 1, 18, 'Чисто мужские/женские части', 'Выведите названия частей, состоящих исключительно из мужчин или женщин. Назовите столбец military_unit_name и отсортируйте результат по алфавиту. Это редкие случаи, характерные для отдельных родов войск', 'Примените `UNION` для объединения результатов двух подзапросов с `EXISTS` и `NOT EXISTS`', NULL, '{"data": [["101-й полк НКВД"], ["101-й учебный полк"], ["106-я стрелковая дивизия"], ["14-я отдельная штрафная рота"], ["18-я дивизия СС \"Хорст Вессель\""], ["1-й чехословацкий отдельный батальон"], ["1-я гвардейская танковая армия"], ["1-я морская бригада"], ["225-й отдельный инженерный батальон"], ["28-я дивизия народного ополчения"], ["2-я ударная армия"], ["369-й отдельный батальон морской пехоты"], ["37-й гвардейский миномётный полк"], ["3-я воздушная армия"], ["585-й женский авиаполк"], ["88-й отдельный лыжный батальон"], ["8-я гвардейская армия"], ["Отдельная медико-санитарная рота"], ["Отдельный батальон связи №45"], ["Отдельный отряд собак-истребителей танков"]], "columns": ["military_unit_name"], "row_count": 20}', '{medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (46, 1, 19, 'Накопление ресурсов', 'Рассчитайте накопленный объем боеприпасов, поставляемых в части за 1942 год. Выведите столбцы unit_id, month, total_ammo и отсортируйте результат по первому столбцу. Это отразит логистические усилия в критический период', 'Используйте оконную функцию `SUM` с сортировкой по месяцам', NULL, '{"data": [[1, 3.0, 50000.0], [2, 3.0, 50000.0], [6, 12.0, 20000.0], [13, 3.0, 30000.0], [18, 3.0, 40000.0], [21, 3.0, 50000.0], [26, 3.0, 70000.0]], "columns": ["unit_id", "month", "total_ammo"], "row_count": 7}', '{supply,window,medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (73, 1, 21, 'Долгосрочная служба', 'Выявите солдат, чья служба длилась более трех лет. Выведите полное имя солдата и длительность службы в днях (days). Отсортируйте результат от меньшей длительности к большей. Это может указывать на ветеранов, участвовавших в ключевых операциях', 'Рассчитайте разницу между датами начала и окончания службы с помощью `AGE`', NULL, '{"data": [["Громов Михаил Сергеевич", 1126], ["Кузнецов Пётр Васильевич", 1153], ["Гришин Алексей Петрович", 1245]], "columns": ["full_name", "days"], "row_count": 3}', '{medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (50, 1, 22, 'Союзники врага', 'Определите все вражеские части, участвовавшие в Курской битве. Это поможет понять структуру сил противника. Выведите только unit_name.', 'Используйте рекурсивный CTE для поиска связанных через таблицу союзов', NULL, '{"data": [["Танковая группа \"Кемпф\""], ["505-й тяжёлый танковый батальон"], ["503-й тяжёлый танковый батальон"], ["505-й инженерный батальон"], ["Эскадра SG2 \"Иммельман\""], ["12-я танковая дивизия"], ["Эскадра KG27 \"Бёльке\""], ["337-я пехотная дивизия"]], "columns": ["unit_name"], "row_count": 8}', '{cte,medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (58, 2, 4, 'Снаряжение элитных частей', 'Определите, какие типы снаряжения чаще всего используются в частях с эффективностью выше среднего. Вычисленный столбец назовите total. Отсортируйте результат в алфавитном порядке. Это поможет понять, какие ресурсы влияют на успех', 'Примените подзапрос для вычисления средней эффективности и `GROUP BY` для типов снаряжения', NULL, '{"data": [["артиллерия", 1], ["боеприпасы", 6], ["медицина", 3], ["миномёты", 1], ["противотанковые", 1], ["реактивные снаряды", 1], ["самолёты", 1], ["танки", 2]], "columns": ["equipment_type", "total"], "row_count": 8}', '{supply,hard}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (55, 2, 1, 'Рейтинг героев', 'Ранжируйте солдат по количеству наград в их частях. Выведите имя солдата, название подразделения (unit_name),	количество медалей (medals_count) и вычисленный ранг (medal_rank). Фамилии солдат выведите в алфавитном порядке. Это основа для определения самых отличившихся бойцов', 'Используйте `DENSE_RANK()` с группировкой по частям и сортировкой по наградам', NULL, '{"data": [["Белов Алексей Николаевич", "150-я стрелковая дивизия", 1, 1], ["Белов Дмитрий Николаевич", "1-й отдельный чехословацкий батальон", 0, 1], ["Беляев Павел Дмитриевич", "88-й отдельный лыжный батальон", 0, 1], ["Васнецова Татьяна Дмитриевна", "106-я стрелковая дивизия", 1, 1], ["Волкова Елена Сергеевна", "1-я морская бригада", 0, 1], ["Воронцова Лидия Павловна", "1-й отдельный чехословацкий батальон", 0, 1], ["Горбачёв Алексей Дмитриевич", "28-я дивизия народного ополчения", 0, 1], ["Гришин Алексей Петрович", "101-й учебный полк", 0, 1], ["Громова Екатерина Ивановна", "46-й гвардейский ночной бомбардировочный полк", 0, 1], ["Громов Михаил Сергеевич", "2-я ударная армия", 1, 1], ["Жукова Елена Викторовна", "18-я дивизия СС \"Хорст Вессель\"", 0, 1], ["Жуков Андрей Григорьевич", "16-я воздушная армия", 1, 1], ["Жуковский Виктор Михайлович", "46-й гвардейский ночной бомбардировочный полк", 0, 1], ["Зайцева Людмила Михайловна", "150-я стрелковая дивизия", 1, 1], ["Иванов Алексей Петрович", "316-я стрелковая дивизия", 1, 1], ["Ковалёва Ольга Дмитриевна", "Отдельный отряд собак-миноискателей", 0, 1], ["Ковалёв Сергей Николаевич", "369-й отдельный батальон морской пехоты", 0, 1], ["Козлов Николай Семёнович", "1-я гвардейская танковая армия", 0, 2], ["Крылова Надежда Фёдоровна", "Отдельный батальон связи №45", 0, 1], ["Кузнецов Артём Игоревич", "Отдельный отряд собак-миноискателей", 0, 1], ["Кузнецов Пётр Васильевич", "1-я гвардейская танковая армия", 1, 1], ["Мельникова Галина Ивановна", "1-й чехословацкий отдельный батальон", 0, 1], ["Морозова Анна Сергеевна", "101-й инженерно-сапёрный батальон", 0, 1], ["Морозов Иван Кузьмич", "14-я отдельная штрафная рота", 0, 1], ["Новиков Александр Иванович", "3-я воздушная армия", 1, 1], ["Орлова Вера Павловна", "8-я гвардейская армия", 1, 1], ["Орлов Денис Сергеевич", "225-й отдельный инженерный батальон", 0, 1], ["Павлов Яков Фёдорович", "62-я армия", 1, 1], ["Петров Дмитрий Иванович", "62-я армия", 1, 1], ["Семёнова Валентина Михайловна", "101-й полк НКВД", 0, 1], ["Сидорова Екатерина Петровна", "Отдельный отряд собак-истребителей танков", 0, 1], ["Смирнова Анна Васильевна", "62-я армия", 1, 1], ["Смирнов Василий Иванович", "37-й гвардейский миномётный полк", 0, 1], ["Соколова Ольга Ивановна", "16-я воздушная армия", 1, 1], ["Соколовская Надежда Викторовна", "64-я стрелковая дивизия", 0, 1], ["Ткаченко Григорий Петрович", "Отдельная медико-санитарная рота", 0, 1], ["Ткаченко Иван Григорьевич", "64-я стрелковая дивизия", 0, 1], ["Фёдорова Мария Ивановна", "316-я стрелковая дивизия", 0, 2], ["Фёдоров Игорь Васильевич", "585-й женский авиаполк", 0, 1], ["Фролов Павел Сергеевич", "101-й инженерно-сапёрный батальон", 0, 1]], "columns": ["full_name", "unit_name", "medals_count", "medal_rank"], "row_count": 40}', '{first_any_level,hard}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (78, 2, 2, 'Сравнение стратегий', 'Сравните среднюю эффективность частей, участвовавших в стратегических и локальных операциях. Это покажет разницу в результативности. Назовите столбцы battle_group и avg_efficiency. Назовите средние эффективности "Стратегические битвы" и "Локальные операции"', 'Примените `CASE` для классификации битв и `AVG` для сравнения', NULL, '{"data": [["Локальные операции", 88.07142857142857], ["Стратегические битвы", 85.0875]], "columns": ["battle_group", "avg_efficiency"], "row_count": 2}', '{hard}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (57, 2, 3, 'Анализ интервалов поставок', 'Определите среднее время между пополнениями снаряжения для каждой части. Выведите столбцы unit_name, equipment_type, last_replenishment, prev_replenishment (дата предыдущего пополнения), next_replenishment (дата следующего пополнения), days_between (интервал). Это поможет выявить логистические задержки или перебои', 'Примените `LAG()` для получения предыдущей даты пополнения и рассчитайте разницу между датами', NULL, '{"data": [["316-я стрелковая дивизия", "оружие", "1942-03-01", null, "1942-03-05", null], ["316-я стрелковая дивизия", "боеприпасы", "1942-03-05", "1942-03-01", "1942-05-10", 4], ["316-я стрелковая дивизия", "связь", "1942-05-10", "1942-03-05", null, 66], ["62-я армия", "боеприпасы", "1942-03-05", null, "1942-11-10", null], ["62-я армия", "артиллерия", "1942-11-10", "1942-03-05", "1943-01-10", 250], ["62-я армия", "медицина", "1943-01-10", "1942-11-10", "1943-12-01", 61], ["62-я армия", "медицина", "1943-12-01", "1943-01-10", null, 325], ["1-я гвардейская танковая армия", "танки", "1943-07-05", null, null, null], ["150-я стрелковая дивизия", "миномёты", "1944-01-15", null, null, null], ["16-я воздушная армия", "самолёты", "1943-05-01", null, null, null], ["7-я гвардейская миномётная дивизия", "боеприпасы", "1942-12-01", null, "1942-12-01", null], ["7-я гвардейская миномётная дивизия", "реактивные снаряды", "1942-12-01", "1942-12-01", null, 0], ["2-я ударная армия", "инженерное", "1943-08-14", null, null, null], ["8-я гвардейская армия", "танки", "1944-10-01", null, null, null], ["3-я воздушная армия", "авиабомбы", "1943-09-05", null, null, null], ["106-я стрелковая дивизия", "противотанковые", "1944-02-28", null, null, null], ["1-я морская бригада", "медицина", "1942-03-05", null, "1942-03-05", null], ["1-я морская бригада", "миномёты", "1942-03-05", "1942-03-05", "1942-06-06", 0], ["1-я морская бригада", "миномёты", "1942-06-06", "1942-03-05", null, 93], ["Отдельная медико-санитарная рота", "медицина", "1942-03-05", null, "1942-03-05", null], ["Отдельная медико-санитарная рота", "боеприпасы", "1942-03-05", "1942-03-05", null, 0], ["585-й женский авиаполк", "боеприпасы", "1942-03-05", null, null, null], ["37-й гвардейский миномётный полк", "боеприпасы", "1942-03-05", null, null, null], ["64-я стрелковая дивизия", "боеприпасы", "1942-03-05", null, null, null]], "columns": ["unit_name", "equipment_type", "last_replenishment", "prev_replenishment", "next_replenishment", "days_between"], "row_count": 24}', '{window,hard}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (81, 2, 5, 'Живучесть подразделений', 'Для каждого воинского подразделения рассчитайте: общую продолжительность участия в боях (разница между датой последнего и первого боя), количество боёв, в которых оно участвовало, количество солдат с безвозвратными потерями («убит», «пропал без вести»). На основе этих данных вычислите среднее количество потерь на один бой, определите процентильное положение подразделения по продолжительности участия в боях (чем дольше, тем выше процентиль). Выведите название подразделения (unit_name), общую продолжительность участия в боях (total_duration), количество боёв (battles_count), количество потерь (losses), средние потери на бой (loss_per_battle_ratio), округлённые до 2 знаков, процентиль по продолжительности (survival_percentile), рассчитанный как PERCENT_RANK() по убыванию total_duration. Отсортируйте результат по убыванию общей продолжительности участия в боях. Это покажет, какие подразделения были наиболее устойчивыми. Необходимо вывести колонки unit_name, total_duration, battles_count, losses, loss_per_battle_ratio, survival_percentile по убыванию общей продолжительности сражений.', 'Используйте `MIN()` и `MAX()` для дат сражений, а также `ROUND` для расчета соотношения потерь', NULL, '{"data": [["14-я отдельная штрафная рота", 1190, 1, 0, 0.0, 0.0], ["Отдельный отряд собак-истребителей танков", 871, 1, 0, 0.0, 0.043478260869565216], ["3-я воздушная армия", 447, 1, 1, 1.0, 0.08695652173913043], ["101-й учебный полк", 441, 1, 0, 0.0, 0.13043478260869565], ["101-й инженерно-сапёрный батальон", 441, 1, 0, 0.0, 0.13043478260869565], ["46-й гвардейский ночной бомбардировочный полк", 247, 1, 0, 0.0, 0.21739130434782608], ["37-й гвардейский миномётный полк", 247, 1, 1, 1.0, 0.21739130434782608], ["18-я дивизия СС \"Хорст Вессель\"", 202, 1, 0, 0.0, 0.30434782608695654], ["28-я дивизия народного ополчения", 200, 1, 0, 0.0, 0.34782608695652173], ["316-я стрелковая дивизия", 200, 1, 0, 0.0, 0.34782608695652173], ["1-й чехословацкий отдельный батальон", 200, 1, 0, 0.0, 0.34782608695652173], ["225-й отдельный инженерный батальон", 200, 1, 0, 0.0, 0.34782608695652173], ["Отдельная медико-санитарная рота", 89, 1, 1, 1.0, 0.5217391304347826], ["1-й отдельный чехословацкий батальон", 89, 1, 2, 2.0, 0.5217391304347826], ["88-й отдельный лыжный батальон", 62, 1, 0, 0.0, 0.6086956521739131], ["64-я стрелковая дивизия", 62, 1, 0, 0.0, 0.6086956521739131], ["16-я воздушная армия", 62, 1, 0, 0.0, 0.6086956521739131], ["Отдельный отряд собак-миноискателей", 49, 1, 0, 0.0, 0.7391304347826086], ["585-й женский авиаполк", 49, 1, 1, 1.0, 0.7391304347826086], ["62-я армия", 49, 1, 1, 1.0, 0.7391304347826086], ["Отдельный батальон связи №45", 49, 1, 0, 0.0, 0.7391304347826086], ["106-я стрелковая дивизия", 24, 1, 0, 0.0, 0.9130434782608695], ["1-я гвардейская танковая армия", 22, 1, 1, 1.0, 0.9565217391304348], ["369-й отдельный батальон морской пехоты", 7, 1, 0, 0.0, 1.0]], "columns": ["unit_name", "total_duration", "battles_count", "losses", "loss_per_battle_ratio", "survival_percentile"], "row_count": 24}', '{hard}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (80, 2, 6, 'Полный портрет части', 'Сформируйте сводку по каждой воинской части: количество солдат, снаряжения, участие в битвах и полученные награды. Это основа для комплексного анализа. Выведите колонки unit_name, soldiers_total, equipment_types, battles_participated, medals_received. Выведите результат по убыванию количества солдат.', 'Используйте `LEFT JOIN` для объединения таблиц и агрегатные функции (`COUNT`, `STRING_AGG`)', NULL, '{"data": [["62-я армия", 3, 4, 1, "Герой Советского Союза, Медаль \"За взятие Берлина\", Орден Отечественной войны"], ["Отдельный отряд собак-миноискателей", 2, 0, 1, null], ["150-я стрелковая дивизия", 2, 1, 0, "Медаль \"За оборону Сталинграда\", Медаль \"За отвагу\""], ["16-я воздушная армия", 2, 1, 1, "Медаль \"За оборону Москвы\", Орден Красной Звезды"], ["1-й отдельный чехословацкий батальон", 2, 0, 1, null], ["1-я гвардейская танковая армия", 2, 1, 1, "Герой Советского Союза"], ["316-я стрелковая дивизия", 2, 3, 1, "Медаль \"За отвагу\""], ["46-й гвардейский ночной бомбардировочный полк", 2, 0, 1, null], ["64-я стрелковая дивизия", 2, 1, 1, null], ["101-й инженерно-сапёрный батальон", 2, 0, 1, null], ["1-й чехословацкий отдельный батальон", 1, 0, 1, null], ["1-я морская бригада", 1, 3, 0, null], ["225-й отдельный инженерный батальон", 1, 0, 1, null], ["28-я дивизия народного ополчения", 1, 0, 1, null], ["2-я ударная армия", 1, 1, 0, "Орден Отечественной войны"], ["Отдельная медико-санитарная рота", 1, 2, 1, null], ["369-й отдельный батальон морской пехоты", 1, 0, 1, null], ["37-й гвардейский миномётный полк", 1, 1, 1, null], ["3-я воздушная армия", 1, 1, 1, "Орден Красной Звезды"], ["Отдельный батальон связи №45", 1, 0, 1, null], ["585-й женский авиаполк", 1, 1, 1, null], ["101-й полк НКВД", 1, 0, 0, null], ["101-й учебный полк", 1, 0, 1, null], ["106-я стрелковая дивизия", 1, 1, 1, "Медаль \"Партизану Отечественной войны\""], ["14-я отдельная штрафная рота", 1, 0, 1, null], ["Отдельный отряд собак-истребителей танков", 1, 0, 1, null], ["8-я гвардейская армия", 1, 1, 0, "Орден Славы"], ["18-я дивизия СС \"Хорст Вессель\"", 1, 0, 1, null], ["88-й отдельный лыжный батальон", 1, 0, 1, null], ["7-я гвардейская миномётная дивизия", 0, 2, 0, null]], "columns": ["unit_name", "soldiers_total", "equipment_types", "battles_participated", "medals_received"], "row_count": 30}', '{hard}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (59, 2, 7, 'Критический дефицит', 'Для анализа состояния снабжения воинских подразделений необходимо выявить снаряжение, количество которого значительно отклоняется от среднего уровня по каждому типу. Для этого требуется рассчитать среднее количество и стандартное отклонение для каждого типа снаряжения (equipment_type) по всем подразделениям, а затем определить, в каких именно частях и какие конкретно предметы снаряжения находятся в дефиците. Каждая единица снаряжения должна быть классифицирована как «Критический дефицит», если её количество ниже среднего на полторы стандартные девиации, как «Дефицит», если количество ниже среднего, но не достигает уровня критического дефицита, и как «Норма» в остальных случаях. В результате должен быть выведен список всего снаряжения с указанием его типа, названия, названия подразделения, количества и статуса, отсортированный сначала по типу снаряжения, а затем по возрастанию количества, чтобы наглядно выявить потенциальные узкие места в системе снабжения', 'Примените оконные функции (`AVG`, `STDDEV`)', NULL, '{"data": [["Винтовка Мосина", 1200], ["Аптечки полевые", 350], ["76-мм дивизионная пушка ЗИС-3", 24], ["Т-34", 58], ["БМ-13 \"Катюша\"", 12], ["Ил-2", 45], ["М-31", 1500], ["Сапёрная лопатка", 850], ["ИС-2", 42], ["ФАБ-100", 3200], ["ПТРД", 68], ["Радиостанция РБМ", 15], ["Плазменные флаконы", 480]], "columns": ["item_name", "quantity"], "row_count": 13}', '{supply,hard}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (60, 2, 8, 'Топ вражеских частей', 'Для анализа тактики противника требуется определить три вражеских подразделения, одержавших наибольшее количество побед над советскими войсками. Для этого необходимо проанализировать все бои, в которых вражеские подразделения участвовали, и выявить те сражения, где результат не указывал на победу СССР. В каждом таком бою нужно подсчитать количество безвозвратных потерь среди советских солдат, проходивших службу в подразделениях, участвовавших в этом бою, и с помощью ранжирования определить, какое из вражеских подразделений нанесло наибольший урон, считая его победителем в случае, если в бою было несколько вражеских подразделений. Затем для каждого вражеского подразделения необходимо подсчитать общее количество таких побед (по числу боёв, где оно заняло первое место по урону) и суммарное количество советских потерь, понесённых в этих боях. В результате следует вывести названия трёх лучших по числу побед подразделений, а также количество их побед и общее число потерь среди советских солдат в этих сражениях, отсортировав сначала по убыванию числа побед, а затем — по убыванию суммарных потерь. Выведите unit_name, victories и total_soviet_losses по убыванию  victories и total_soviet_losses.', 'Используйте `RANK()`, `COUNT` с фильтрацией по результату битв и `LIMIT 3`', NULL, '{"data": [["17-я танковая дивизия", 1, 2.0], ["1-я танковая дивизия СС \"Лейбштандарт Адольф Гитлер\"", 1, 1.0], ["9-я армия", 1, 1.0]], "columns": ["unit_name", "victories", "total_soviet_losses"], "row_count": 3}', '{window,hard}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (82, 2, 9, 'Прогноз износа техники', 'Для прогнозирования будущих потребностей в ремонте и замене снаряжения необходимо проанализировать его расход по годам с использованием сглаживающего алгоритма. Для каждого типа снаряжения (equipment_type) и каждого года (issue_date) требуется рассчитать коэффициент потерь как отношение количества снаряжения, выданного солдатам, к количеству солдат, проходивших службу в тот же год, чтобы учесть масштабы деятельности частей. Данный коэффициент следует сгладить с помощью трёхлетнего скользящего среднего (включая текущий год и два предыдущих), чтобы устранить случайные колебания и выявить общую тенденцию. Выведите тип снаряжения, год, исходный коэффициент потерь и сглаженное значение, отсортировав результат сначала по типу снаряжения, а затем по году в порядке возрастания', 'Используйте CTE для подсчёта примените AVG(...) OVER (ORDER BY year ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) для сглаживания', NULL, '{"data": [["авиабомбы", 1943.0, 2.1818, 2.1818], ["артиллерия", 1942.0, 0.0769, 0.0769], ["боеприпасы", 1942.0, 9.2308, 9.2308], ["инженерное", 1943.0, 0.0909, 0.0909], ["медицина", 1943.0, 0.7273, 0.7273], ["миномёты", 1944.0, 20.0, 20.0], ["оружие", 1942.0, 0.0769, 0.0769], ["противотанковые", 1944.0, 0.1667, 0.1667], ["самолёты", 1943.0, 0.0909, 0.0909], ["связь", 1942.0, 0.0769, 0.0769], ["танки", 1943.0, 0.0909, 0.0909], ["танки", 1944.0, 0.1667, 0.1288]], "columns": ["equipment_type", "year", "loss_ratio", "smoothed_ratio"], "row_count": 12}', '{hard}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (61, 2, 10, 'Эффективность наград', 'Для оценки соответствия воинских наград реальным результатам в бою необходимо проанализировать подразделения, которые получили наибольшее количество наград. Для каждого такого подразделения следует определить, какие именно награды ему были присвоены, и подсчитать общее количество раз, когда они были вручены (всего наградовано солдат). Далее, для этих же подразделений необходимо подсчитать количество боёв, в которых они одержали победу (результат боя — «победа»), и общее число солдат с безвозвратными потерями («убит» и «пропал без вести»). На основе этих данных рассчитайте соотношение побед к числу наград (victory_per_medal) и потерь к числу наград (death_per_medal) для каждой награды, чтобы оценить, насколько боевые достижения и потери сопоставимы с полученным признанием. Выведите название подразделения, название награды, количество награждений, количество погибших, число побед и два расчётных показателя, отсортировав результат по убыванию соотношения побед к наградам, при этом строки с нулевым значением victory_per_medal должны располагаться в конце списка.', 'Используйте CTE. Объедините данные по unit_id и medal_id. Рассчитайте victory_per_medal и death_per_medal с округлением. В сортировке используйте CASE, чтобы вывести нули в victory_per_medal в конец', NULL, '{"data": [["3-я воздушная армия", "Орден Красной Звезды", 1, 0, 1, 1.0, 0.0], ["150-я стрелковая дивизия", "Медаль \"За оборону Сталинграда\"", 1, 0, 0, 0.0, 0.0], ["106-я стрелковая дивизия", "Медаль \"Партизану Отечественной войны\"", 1, 0, 0, 0.0, 0.0], ["16-я воздушная армия", "Орден Красной Звезды", 1, 0, 0, 0.0, 0.0], ["150-я стрелковая дивизия", "Медаль \"За отвагу\"", 1, 0, 0, 0.0, 0.0], ["8-я гвардейская армия", "Орден Славы", 1, 0, 0, 0.0, 0.0], ["62-я армия", "Медаль \"За взятие Берлина\"", 1, 0, 0, 0.0, 0.0], ["1-я гвардейская танковая армия", "Герой Советского Союза", 1, 0, 0, 0.0, 0.0], ["62-я армия", "Орден Отечественной войны", 1, 0, 0, 0.0, 0.0], ["62-я армия", "Герой Советского Союза", 1, 0, 0, 0.0, 0.0], ["316-я стрелковая дивизия", "Медаль \"За отвагу\"", 1, 0, 0, 0.0, 0.0], ["2-я ударная армия", "Орден Отечественной войны", 1, 0, 0, 0.0, 0.0], ["16-я воздушная армия", "Медаль \"За оборону Москвы\"", 1, 0, 0, 0.0, 0.0]], "columns": ["unit_name", "medal_name", "awarded", "deaths", "victories", "victory_per_medal", "death_per_medal"], "row_count": 13}', '{window,hard}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (83, 2, 11, 'Сезонность боевых действий', 'Для выявления возможных сезонных закономерностей в боевых действиях советских войск необходимо определить, в какие месяцы года они чаще всего одерживали победы. Для этого требуется проанализировать данные о боях, в которых участвовали советские подразделения, и выделить те сражения, исход которых соответствовал победе СССР (например, строка result содержит "победа СССР", "успешно", "советские войска одержали верх" и т.п.). Для каждой победы следует извлечь месяц из даты окончания боя, так как именно к этому моменту становится ясен её итог. Далее необходимо подсчитать количество побед, одержанных в каждом месяце года, и ранжировать результат по убыванию количества побед. Выведите месяц (в виде числа от 1 до 12), его название (для удобства), общее количество побед в этом месяце и процент всех побед, приходящихся на этот месяц, от общего числа побед за весь период. Отсортируйте результат по убыванию количества побед', 'Используйте `EXTRACT(MONTH)` для группировки и `COUNT` с фильтрацией по результату битв', NULL, '{"data": [[4.0, "April", 1, 100.0]], "columns": ["month_num", "month_name", "victory_count", "victory_percentage"], "row_count": 1}', '{hard}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (62, 2, 12, 'Стоимость победы', 'Для анализа ценности побед в боевых действиях требуется определить, какие битвы, несмотря на успех, были наиболее «дорогими» в терминах потерь среди солдат и затрат ресурсов. Для каждой битвы необходимо рассчитать общее количество безвозвратных потерь (солдаты со статусом «убит» или «пропал без вести»), участвовавших в ней, а также среднюю исходную боевую эффективность подразделений, принимавших в ней участие. Дополнительно нужно подсчитать количество единиц снаряжения, использованного солдатами, участвовавшими в битве, что отразит объём израсходованных материальных ресурсов. На основе этих данных следует вычислить условный «стоимостной коэффициент» битвы (cost_ratio) как отношение числа потерь к средней боевой эффективности — чем выше этот коэффициент, тем «дороже» победа. Затем необходимо проранжировать все битвы по убыванию числа потерь (loss_rank) и по убыванию средней эффективности (eff_rank), где ранг 1 присваивается наибольшему значению. В результате нужно вывести название битвы, количество потерь, среднюю боевую эффективность, объём использованного снаряжения, ранги по потерям и эффективности, а также стоимостной коэффициент, отсортировав итоговый список по убыванию cost_ratio', 'Используйте `RANK()` и арифметические операции с агрегатными функциями', NULL, '{"data": [["Оборона Севастополя", 0, 96.6, 0, 1, 1, 0.0], ["Битва за Берлин", 0, 95.0, 2, 1, 2, 0.0], ["Корсунь-Шевченковская операция", 0, 89.3, 1, 1, 3, 0.0], ["Оборона Брестской крепости", 0, 88.9, 0, 1, 4, 0.0], ["Демянская операция", 0, 88.35, 0, 1, 5, 0.0], ["Курская битва", 0, 88.23, 6, 1, 6, 0.0], ["Битва за Москву", 0, 88.1, 0, 1, 7, 0.0], ["Смоленское сражение", 0, 85.07, 4, 1, 8, 0.0], ["Ржевская битва", 0, 85.0, 24, 1, 9, 0.0], ["Блокада Ленинграда", 0, 82.4, 0, 1, 10, 0.0], ["Сталинградская битва", 0, 80.88, 121, 1, 11, 0.0], ["Битва за Кавказ", 0, 78.9, 0, 1, 12, 0.0], ["Оборона Заполярья", 0, 65.8, 0, 1, 13, 0.0], ["Оборона Тулы", 0, 0.0, 0, 1, 14, 0.0], ["Берлинская операция", 0, 0.0, 0, 1, 14, 0.0], ["Пражская операция", 0, 0.0, 0, 1, 14, 0.0], ["Оборона Брестской крепости", 0, 0.0, 0, 1, 14, 0.0], ["Битва при Дебрецене", 0, 0.0, 0, 1, 14, 0.0], ["Операция \"Багратион\"", 0, 0.0, 0, 1, 14, 0.0], ["Висло-Одерская операция", 0, 0.0, 0, 1, 14, 0.0], ["Будапештская операция", 0, 0.0, 0, 1, 14, 0.0], ["Харьковская операция", 0, 0.0, 0, 1, 14, 0.0], ["Битва за Днепр", 0, 0.0, 0, 1, 14, 0.0], ["Таллинский переход", 0, 0.0, 0, 1, 14, 0.0], ["Прорыв блокады Ленинграда", 0, 0.0, 0, 1, 14, 0.0], ["Битва за Воронеж", 0, 0.0, 0, 1, 14, 0.0], ["Керченско-Эльтигенская операция", 0, 0.0, 0, 1, 14, 0.0], ["Балатонская операция", 0, 0.0, 0, 1, 14, 0.0], ["Восточно-Прусская операция", 0, 0.0, 0, 1, 14, 0.0], ["Маньчжурская операция", 0, 0.0, 0, 1, 14, 0.0]], "columns": ["battle_name", "losses", "avg_efficiency", "equipment_used", "loss_rank", "eff_rank", "cost_ratio"], "row_count": 30}', '{window,hard}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (84, 3, 1, 'Пространство имён', 'Отряд занял немецкий вычислительный узел; база пуста — ни одной таблицы, ни одного объекта. Прежде чем вносить разведданные, подпольному архиву нужно своё пространство имён, чтобы не смешаться с тем, что осталось от немцев.

Создайте схему podpolye — отдельное пространство имён для подпольной базы.', 'Пространство имён создаётся одним оператором: CREATE SCHEMA <имя>. Схема — это «папка» для таблиц; больше в этом задании ничего не требуется.', 'CREATE SCHEMA podpolye', '{"mode": "model", "setup": [], "expect": [{"args": {"name": "podpolye"}, "probe": "schema_exists", "title": "схема подполья создана", "value": true}, {"args": {"name": "public"}, "probe": "schema_exists", "title": "схема public не тронута", "value": true}, {"args": {"schema": "podpolye", "grantee": "PUBLIC"}, "probe": "schema_privs", "title": "посторонним схему не открывали", "value": []}, {"args": {}, "probe": "all_roles", "title": "посторонних ролей не заводили", "value": []}], "reveal": "Что проверяется: схема подполья создана; схема public не тронута; посторонним схему не открывали; посторонних ролей не заводили."}', '{ddl,schema}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (85, 3, 2, 'Настройка базы', 'Центр принимает донесения по единому времени, а набирать «podpolye.» перед каждым именем таблицы в полутьме — верный способ ошибиться. Семён требует настроить базу один раз и навсегда.

Настройте базу quest_sandbox: часовой пояс по умолчанию — ''UTC'', а путь поиска схем — сначала podpolye, затем public.', 'Параметры уровня базы задаются оператором изменения базы данных, а не правкой файла настроек: ALTER DATABASE <имя> SET <параметр> TO <значение>. Здесь таких оператора два — по одному на каждый параметр.', 'ALTER DATABASE quest_sandbox SET timezone TO ''UTC''; ALTER DATABASE quest_sandbox SET search_path TO podpolye, public', '{"mode": "model", "setup": ["CREATE SCHEMA podpolye"], "expect": [{"args": {"db": "quest_sandbox"}, "probe": "db_settings", "title": "настройки базы", "value": [["search_path", "podpolye,public"], ["timezone", "UTC"]]}, {"args": {"name": "podpolye"}, "probe": "schema_exists", "title": "схема на месте", "value": true}], "reveal": "Что проверяется: настройки базы; схема на месте."}', '{ddl,config}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (86, 3, 3, 'Таблица складов', 'Первое, что нужно Центру, — учёт немецких складов: номер, название, сектор города и вместимость. Номер — то, чем склад отличается от всех остальных; безымянный склад разведданными не является, а вот вместимость известна не всегда.

Создайте таблицу podpolye.depots: depot_id — целое число, первичный ключ; depot_name — строка не длиннее 40 символов, обязательная; sector — ровно один символ, обязательный; capacity_t — целое число, может оставаться пустым.', '«Целое число» — тип integer, «строка не длиннее N» — varchar(N), «ровно один символ» — char(1). Обязательность — NOT NULL, а первичный ключ можно объявить прямо в определении столбца: depot_id integer PRIMARY KEY.', 'CREATE TABLE podpolye.depots(
    depot_id   integer PRIMARY KEY,
    depot_name varchar(40) NOT NULL,
    sector     char(1) NOT NULL,
    capacity_t integer)', '{"mode": "model", "setup": ["CREATE SCHEMA podpolye"], "expect": [{"args": {"table": "podpolye.depots"}, "probe": "columns", "title": "столбцы таблицы складов", "value": [["depot_id", "integer", null, true, false], ["depot_name", "character varying", 40, true, false], ["sector", "character", 1, true, false], ["capacity_t", "integer", null, false, false]]}, {"args": {"table": "podpolye.depots"}, "probe": "primary_key", "title": "первичный ключ складов", "value": ["depot_id"]}, {"args": {"table": "podpolye.depots"}, "probe": "uniques", "title": "лишних ограничений уникальности нет", "value": []}, {"args": {"table": "podpolye.depots"}, "probe": "public_privs", "title": "права никому не раздавали", "value": []}], "reveal": "Что проверяется: столбцы таблицы складов; первичный ключ складов; лишних ограничений уникальности нет; права никому не раздавали."}', '{ddl,table,constraint}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (87, 3, 4, 'Заплата на сектор', 'Наблюдатель при свече вывел «8» вместо «B» — и база приняла склад в несуществующем секторе. Город поделён ровно на четыре сектора: A, B, C и D. Дыра должна закрыться этой же ночью.

Добавьте к таблице podpolye.depots ограничение-проверку, которое разрешает в столбце sector только значения ''A'', ''B'', ''C'' и ''D''.', 'Ограничение добавляется к готовой таблице: ALTER TABLE ... ADD CONSTRAINT <имя> CHECK (условие). Условие «одно из перечисленных значений» короче всего записывается через IN: sector IN (''A'',''B'',''C'',''D'').', 'ALTER TABLE podpolye.depots ADD CONSTRAINT depots_sector_chk CHECK (sector IN (''A'',''B'',''C'',''D''))', '{"mode": "model", "setup": ["CREATE SCHEMA podpolye", "CREATE TABLE podpolye.depots(\n    depot_id   integer PRIMARY KEY,\n    depot_name varchar(40) NOT NULL,\n    sector     char(1) NOT NULL,\n    capacity_t integer)"], "expect": [{"args": {"cases": [{"row": {"sector": "A", "depot_id": 99, "capacity_t": 10, "depot_name": "Проба"}, "label": "A"}, {"row": {"sector": "B", "depot_id": 99, "capacity_t": 10, "depot_name": "Проба"}, "label": "B"}, {"row": {"sector": "C", "depot_id": 99, "capacity_t": 10, "depot_name": "Проба"}, "label": "C"}, {"row": {"sector": "D", "depot_id": 99, "capacity_t": 10, "depot_name": "Проба"}, "label": "D"}, {"row": {"sector": "E", "depot_id": 99, "capacity_t": 10, "depot_name": "Проба"}, "label": "E"}, {"row": {"sector": "X", "depot_id": 99, "capacity_t": 10, "depot_name": "Проба"}, "label": "X"}, {"row": {"sector": "Z", "depot_id": 99, "capacity_t": 10, "depot_name": "Проба"}, "label": "Z"}, {"row": {"sector": "a", "depot_id": 99, "capacity_t": 10, "depot_name": "Проба"}, "label": "строчная a"}, {"row": {"sector": "Z", "depot_id": 99, "depot_name": "Проба"}, "label": "Z без вместимости"}], "table": "podpolye.depots"}, "probe": "accepts", "title": "какие сектора база принимает", "value": [["A", true], ["B", true], ["C", true], ["D", true], ["E", false], ["X", false], ["Z", false], ["строчная a", false], ["Z без вместимости", false]]}, {"args": {"table": "podpolye.depots"}, "probe": "columns", "title": "столбцы складов не тронуты", "value": [["depot_id", "integer", null, true, false], ["depot_name", "character varying", 40, true, false], ["sector", "character", 1, true, false], ["capacity_t", "integer", null, false, false]]}, {"args": {"table": "podpolye.depots"}, "probe": "primary_key", "title": "первичный ключ на месте", "value": ["depot_id"]}], "reveal": "Что проверяется: какие сектора база принимает; столбцы складов не тронуты; первичный ключ на месте."}', '{ddl,alter,constraint,check}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (88, 3, 5, 'Справочник секторов', 'Сектор — не буква, а самостоятельная вещь с названием: «Заречный», «Вокзальный». Склады должны ссылаться на справочник по-настоящему: сектор, за которым числятся склады, стереть нельзя.

Создайте справочник podpolye.sectors: sector — ровно один символ, первичный ключ; title — строка не длиннее 30 символов, обязательная. Затем свяжите с ним склады: добавьте к podpolye.depots внешний ключ из столбца sector на sectors.sector, запрещающий удалять сектор, пока на него ссылаются склады.', 'Справочник создаётся обычным CREATE TABLE, а связь добавляется к уже существующей таблице: ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY (sector) REFERENCES podpolye.sectors(sector). Запрет удаления «пока есть ссылки» — это ON DELETE RESTRICT.', 'CREATE TABLE podpolye.sectors(sector char(1) PRIMARY KEY, title varchar(30) NOT NULL); ALTER TABLE podpolye.depots ADD CONSTRAINT depots_sector_fk FOREIGN KEY (sector) REFERENCES podpolye.sectors(sector) ON DELETE RESTRICT', '{"mode": "model", "setup": ["CREATE SCHEMA podpolye", "CREATE TABLE podpolye.depots(\n    depot_id   integer PRIMARY KEY,\n    depot_name varchar(40) NOT NULL,\n    sector     char(1) NOT NULL,\n    capacity_t integer)", "ALTER TABLE podpolye.depots ADD CONSTRAINT depots_sector_chk CHECK (sector IN (''A'',''B'',''C'',''D''))"], "expect": [{"args": {"table": "podpolye.sectors"}, "probe": "columns", "title": "столбцы справочника секторов", "value": [["sector", "character", 1, true, false], ["title", "character varying", 30, true, false]]}, {"args": {"table": "podpolye.sectors"}, "probe": "primary_key", "title": "первичный ключ справочника", "value": ["sector"]}, {"args": {"table": "podpolye.depots"}, "probe": "foreign_keys", "title": "внешний ключ складов на сектора", "value": [["sector", "podpolye.sectors", "sector", "запрещает удаление"]]}, {"args": {"table": "podpolye.depots"}, "probe": "columns", "title": "склады остались прежними", "value": [["depot_id", "integer", null, true, false], ["depot_name", "character varying", 40, true, false], ["sector", "character", 1, true, false], ["capacity_t", "integer", null, false, false]]}, {"args": {"table": "podpolye.depots"}, "probe": "primary_key", "title": "первичный ключ складов на месте", "value": ["depot_id"]}], "reveal": "Что проверяется: столбцы справочника секторов; первичный ключ справочника; внешний ключ складов на сектора; склады остались прежними; первичный ключ складов на месте."}', '{ddl,table,foreign_key}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (89, 3, 6, 'Первые донесения', 'Каркас готов, справочник заполнен, база пуста. Три первых склада должны попасть в базу без единой ошибки: что внесено неверно, Центр примет за правду.

Внесите в podpolye.depots три склада: (1, ''Арсенал №1'', ''A'', 800), (2, ''Топливный склад'', ''A'', 450) и (3, ''Продовольственный'', ''B'', 300).', 'Несколько строк вносятся одним оператором: INSERT INTO <таблица>(столбцы) VALUES (...), (...), (...). Строковые значения — в одинарных кавычках, порядок значений должен совпадать с порядком перечисленных столбцов.', 'INSERT INTO podpolye.depots(depot_id, depot_name, sector, capacity_t) VALUES (1,''Арсенал №1'',''A'',800),(2,''Топливный склад'',''A'',450),(3,''Продовольственный'',''B'',300)', '{"mode": "model", "setup": ["CREATE SCHEMA podpolye", "CREATE TABLE podpolye.depots(\n    depot_id   integer PRIMARY KEY,\n    depot_name varchar(40) NOT NULL,\n    sector     char(1) NOT NULL,\n    capacity_t integer)", "ALTER TABLE podpolye.depots ADD CONSTRAINT depots_sector_chk CHECK (sector IN (''A'',''B'',''C'',''D''))", "CREATE TABLE podpolye.sectors(sector char(1) PRIMARY KEY, title varchar(30) NOT NULL)", "INSERT INTO podpolye.sectors VALUES (''A'',''Заречный''),(''B'',''Вокзальный''),(''C'',''Старый город''),(''D'',''Фабричный'')", "ALTER TABLE podpolye.depots ADD CONSTRAINT depots_sector_fk FOREIGN KEY (sector) REFERENCES podpolye.sectors(sector) ON DELETE RESTRICT"], "expect": [{"args": {"table": "podpolye.depots", "columns": ["depot_id", "depot_name", "sector", "capacity_t"], "order_by": "depot_id"}, "probe": "rows", "title": "содержимое таблицы складов", "value": [[1, "Арсенал №1", "A", 800], [2, "Топливный склад", "A", 450], [3, "Продовольственный", "B", 300]]}, {"args": {"table": "podpolye.depots"}, "probe": "columns", "title": "таблица осталась прежней", "value": [["depot_id", "integer", null, true, false], ["depot_name", "character varying", 40, true, false], ["sector", "character", 1, true, false], ["capacity_t", "integer", null, false, false]]}, {"args": {"table": "podpolye.depots"}, "probe": "primary_key", "title": "первичный ключ на месте", "value": ["depot_id"]}], "reveal": "Что проверяется: содержимое таблицы складов; таблица осталась прежней; первичный ключ на месте."}', '{dml,insert}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (104, 4, 9, 'Передоверие', 'Отряд уходит, узел передаётся соседней группе. Их бойцы вам незнакомы — и не должны быть: раздавать доступ своим людям соседи будут сами. Для этого командованию нужно право передавать чтение дальше.

Выдайте роли commanders право читать таблицу podpolye.safehouses так, чтобы она могла передавать это право другим ролям.', 'Возможность передавать право дальше добавляется к обычной выдаче: GRANT SELECT ON podpolye.safehouses TO commanders WITH GRANT OPTION. Именно WITH GRANT OPTION отличает передоверие от простого чтения.', 'GRANT SELECT ON podpolye.safehouses TO commanders WITH GRANT OPTION', '{"mode": "model", "setup": ["CREATE SCHEMA podpolye", "CREATE TABLE podpolye.depots(\n    depot_id   integer PRIMARY KEY,\n    depot_name varchar(40) NOT NULL,\n    sector     char(1) NOT NULL,\n    capacity_t integer)", "INSERT INTO podpolye.depots VALUES (1,''Арсенал №1'',''A'',800),(2,''Топливный склад'',''A'',450),(3,''Продовольственный'',''B'',300)", "CREATE TABLE podpolye.safehouses(\n    house_id  integer PRIMARY KEY,\n    code_name varchar(20) NOT NULL,\n    street    varchar(40) NOT NULL,\n    keeper    varchar(20) NOT NULL,\n    sector    char(1) NOT NULL,\n    is_burnt  boolean NOT NULL DEFAULT false)", "INSERT INTO podpolye.safehouses VALUES (1,''Мельница'',''Заречная, 7'',''Прохор'',''A'',false),(2,''Аптека'',''Соборная, 14'',''Вера'',''A'',true),(3,''Сапожник'',''Кузнечная, 3'',''Пётр'',''B'',false),(4,''Пекарня'',''Хлебный пер., 2'',''Дарья'',''B'',false),(5,''Часовщик'',''Ратушная, 21'',''Артур'',''C'',true),(6,''Прачечная'',''Луговая, 9'',''Клава'',''C'',false)", "CREATE ROLE commanders", "CREATE ROLE scouts", "CREATE ROLE spies", "GRANT USAGE ON SCHEMA podpolye TO commanders", "GRANT ALL PRIVILEGES ON podpolye.depots, podpolye.safehouses TO commanders", "GRANT USAGE ON SCHEMA podpolye TO scouts", "GRANT SELECT, INSERT ON podpolye.depots TO scouts", "GRANT USAGE ON SCHEMA podpolye TO spies", "GRANT SELECT (house_id, sector) ON podpolye.safehouses TO spies", "ALTER TABLE podpolye.safehouses ENABLE ROW LEVEL SECURITY", "CREATE POLICY house_open ON podpolye.safehouses FOR SELECT TO spies USING (is_burnt = false)", "CREATE ROLE grisha LOGIN", "GRANT scouts TO grisha", "ALTER DEFAULT PRIVILEGES IN SCHEMA podpolye GRANT SELECT ON TABLES TO scouts"], "expect": [{"args": {"table": "podpolye.safehouses", "grantee": "commanders"}, "probe": "grantable", "title": "право командования и возможность передачи", "value": [["DELETE", false], ["INSERT", false], ["REFERENCES", false], ["SELECT", true], ["TRIGGER", false], ["TRUNCATE", false], ["UPDATE", false]]}, {"args": {"privs": ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"], "table": "podpolye.safehouses", "grantee": "commanders"}, "probe": "has_privs", "title": "состав прав командования не менялся", "value": [["SELECT", true], ["INSERT", true], ["UPDATE", true], ["DELETE", true], ["TRUNCATE", true], ["REFERENCES", true], ["TRIGGER", true]]}, {"args": {"schema": "podpolye", "grantee": "commanders"}, "probe": "schema_privs", "title": "доступ командования к схеме сохранён", "value": ["USAGE"]}, {"args": {"privs": ["SELECT"], "table": "podpolye.safehouses", "grantees": ["spies", "PUBLIC"]}, "probe": "privs_matrix", "title": "посторонним явки не открывали", "value": [["spies", "SELECT", false], ["PUBLIC", "SELECT", false]]}, {"args": {}, "probe": "all_memberships", "title": "членство ролей не меняли", "value": [["grisha", "scouts"]]}], "reveal": "Что проверяется: право командования и возможность передачи; состав прав командования не менялся; доступ командования к схеме сохранён; посторонним явки не открывали; членство ролей не меняли."}', '{dcl,grant,grant_option}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (90, 3, 7, 'Журнал рейсов', 'Наблюдатели приносят записки о вывозе: склад, дата, тоннаж. Дата почти всегда сегодняшняя — пусть база подставляет её сама. А рейсы склада, ушедшего из учёта, обязаны исчезнуть вместе с ним.

Создайте таблицу podpolye.movements: move_id — целое, первичный ключ; depot_id — целое, обязательное, внешний ключ на podpolye.depots(depot_id), причём вместе со складом должны удаляться и его рейсы; at_date — дата, обязательная, по умолчанию текущая; tons — целое.', 'Связь можно объявить прямо в столбце: depot_id integer NOT NULL REFERENCES podpolye.depots(depot_id) ON DELETE CASCADE — каскад и означает «удалять рейсы вместе со складом». Текущая дата по умолчанию — DEFAULT current_date.', 'CREATE TABLE podpolye.movements(
    move_id  integer PRIMARY KEY,
    depot_id integer NOT NULL REFERENCES podpolye.depots(depot_id) ON DELETE CASCADE,
    at_date  date NOT NULL DEFAULT current_date,
    tons     integer)', '{"mode": "model", "post": ["INSERT INTO podpolye.movements(move_id, depot_id, tons) VALUES (1,1,60),(2,1,38),(3,2,52)"], "setup": ["CREATE SCHEMA podpolye", "CREATE TABLE podpolye.depots(\n    depot_id   integer PRIMARY KEY,\n    depot_name varchar(40) NOT NULL,\n    sector     char(1) NOT NULL,\n    capacity_t integer)", "ALTER TABLE podpolye.depots ADD CONSTRAINT depots_sector_chk CHECK (sector IN (''A'',''B'',''C'',''D''))", "CREATE TABLE podpolye.sectors(sector char(1) PRIMARY KEY, title varchar(30) NOT NULL)", "INSERT INTO podpolye.sectors VALUES (''A'',''Заречный''),(''B'',''Вокзальный''),(''C'',''Старый город''),(''D'',''Фабричный'')", "ALTER TABLE podpolye.depots ADD CONSTRAINT depots_sector_fk FOREIGN KEY (sector) REFERENCES podpolye.sectors(sector) ON DELETE RESTRICT", "INSERT INTO podpolye.depots VALUES (1,''Арсенал №1'',''A'',800),(2,''Топливный склад'',''A'',450),(3,''Продовольственный'',''B'',300)"], "expect": [{"args": {"table": "podpolye.movements"}, "probe": "columns", "title": "столбцы таблицы рейсов", "value": [["move_id", "integer", null, true, false], ["depot_id", "integer", null, true, false], ["at_date", "date", null, true, true], ["tons", "integer", null, false, false]]}, {"args": {"table": "podpolye.movements"}, "probe": "primary_key", "title": "первичный ключ рейсов", "value": ["move_id"]}, {"args": {"table": "podpolye.movements"}, "probe": "foreign_keys", "title": "внешний ключ рейсов на склады", "value": [["depot_id", "podpolye.depots", "depot_id", "удаляет следом"]]}, {"args": {"table": "podpolye.movements", "columns": ["at_date"]}, "probe": "default_kind", "title": "дата подставляется сама", "value": [["at_date", "текущий момент"]]}, {"args": {"table": "podpolye.depots", "value": 1, "column": "depot_id"}, "probe": "delete_allowed", "title": "склад удаляется вместе со своими рейсами", "value": true}, {"args": {"cases": [{"row": {"tons": 5, "move_id": 1, "depot_id": 2}, "label": "повтор номера"}, {"row": {"tons": 5, "move_id": 99, "depot_id": 2}, "label": "новый номер"}], "table": "podpolye.movements"}, "probe": "accepts", "title": "повтор номера рейса и новый номер", "value": [["повтор номера", false], ["новый номер", true]]}], "reveal": "Что проверяется: столбцы таблицы рейсов; первичный ключ рейсов; внешний ключ рейсов на склады; дата подставляется сама; склад удаляется вместе со своими рейсами; повтор номера рейса и новый номер."}', '{ddl,table,foreign_key,default}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (91, 3, 8, 'Груз и вес', 'В таблице рейсов не хватает главного — что именно вывозят. Заодно в базу попал рейс с отрицательным весом: отрицательных тонн не бывает, и база должна знать это сама.

В таблицу podpolye.movements добавьте столбец cargo_ru — строка не длиннее 30 символов, и ограничение, требующее, чтобы значение tons было строго больше нуля.', 'Здесь два отдельных действия над готовой таблицей: ALTER TABLE ... ADD COLUMN cargo_ru varchar(30) и ALTER TABLE ... ADD CONSTRAINT ... CHECK (tons > 0). «Строго больше нуля» — именно >, а не >=.', 'ALTER TABLE podpolye.movements ADD COLUMN cargo_ru varchar(30); ALTER TABLE podpolye.movements ADD CONSTRAINT movements_tons_chk CHECK (tons > 0)', '{"mode": "model", "setup": ["CREATE SCHEMA podpolye", "CREATE TABLE podpolye.depots(\n    depot_id   integer PRIMARY KEY,\n    depot_name varchar(40) NOT NULL,\n    sector     char(1) NOT NULL,\n    capacity_t integer)", "ALTER TABLE podpolye.depots ADD CONSTRAINT depots_sector_chk CHECK (sector IN (''A'',''B'',''C'',''D''))", "CREATE TABLE podpolye.sectors(sector char(1) PRIMARY KEY, title varchar(30) NOT NULL)", "INSERT INTO podpolye.sectors VALUES (''A'',''Заречный''),(''B'',''Вокзальный''),(''C'',''Старый город''),(''D'',''Фабричный'')", "ALTER TABLE podpolye.depots ADD CONSTRAINT depots_sector_fk FOREIGN KEY (sector) REFERENCES podpolye.sectors(sector) ON DELETE RESTRICT", "INSERT INTO podpolye.depots VALUES (1,''Арсенал №1'',''A'',800),(2,''Топливный склад'',''A'',450),(3,''Продовольственный'',''B'',300)", "CREATE TABLE podpolye.movements(\n    move_id  integer PRIMARY KEY,\n    depot_id integer NOT NULL REFERENCES podpolye.depots(depot_id) ON DELETE CASCADE,\n    at_date  date NOT NULL DEFAULT current_date,\n    tons     integer)", "INSERT INTO podpolye.movements(move_id, depot_id, at_date, tons) VALUES (1,1,''1944-09-11'',60),(2,1,''1944-09-15'',38),(3,2,''1944-09-12'',52),(4,3,''1944-09-14'',22),(5,3,''1944-09-18'',45)"], "expect": [{"args": {"table": "podpolye.movements"}, "probe": "columns", "title": "столбцы рейсов после правки", "value": [["move_id", "integer", null, true, false], ["depot_id", "integer", null, true, false], ["at_date", "date", null, true, true], ["tons", "integer", null, false, false], ["cargo_ru", "character varying", 30, false, false]]}, {"args": {"cases": [{"row": {"tons": 10, "move_id": 99, "depot_id": 1}, "label": "10 тонн"}, {"row": {"tons": 5, "move_id": 99, "depot_id": 1}, "label": "5 тонн"}, {"row": {"tons": 1, "move_id": 99, "depot_id": 1}, "label": "1 тонна"}, {"row": {"tons": 0, "move_id": 99, "depot_id": 1}, "label": "ноль"}, {"row": {"tons": -5, "move_id": 99, "depot_id": 1}, "label": "минус пять"}, {"row": {"tons": -100, "move_id": 99, "depot_id": 1}, "label": "минус сто"}], "table": "podpolye.movements"}, "probe": "accepts", "title": "какой вес база принимает", "value": [["10 тонн", true], ["5 тонн", true], ["1 тонна", true], ["ноль", false], ["минус пять", false], ["минус сто", false]]}, {"args": {"table": "podpolye.movements"}, "probe": "foreign_keys", "title": "связь со складами не потеряна", "value": [["depot_id", "podpolye.depots", "depot_id", "удаляет следом"]]}, {"args": {"table": "podpolye.movements"}, "probe": "primary_key", "title": "первичный ключ рейсов на месте", "value": ["move_id"]}, {"args": {"table": "podpolye.movements", "columns": ["move_id", "depot_id", "tons"], "order_by": "move_id"}, "probe": "rows", "title": "рейсы на месте", "value": [[1, 1, 60], [2, 1, 38], [3, 2, 52], [4, 3, 22], [5, 3, 45]]}], "reveal": "Что проверяется: столбцы рейсов после правки; какой вес база принимает; связь со складами не потеряна; первичный ключ рейсов на месте; рейсы на месте."}', '{ddl,alter,constraint,check}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (92, 3, 9, 'Указатель', 'Счётная машина перебирает весь журнал рейсов ради одной сводки по складу. Нужен указатель по столбцу связи — и он не обязан быть уникальным: с одного склада рейсов много.

Постройте по столбцу depot_id таблицы podpolye.movements обычный, не уникальный индекс.', 'Индекс создаётся оператором CREATE INDEX <имя> ON <таблица>(<столбец>). Слово UNIQUE добавлять не нужно — как раз потому, что значения в depot_id повторяются.', 'CREATE INDEX movements_depot_idx ON podpolye.movements(depot_id)', '{"mode": "model", "setup": ["CREATE SCHEMA podpolye", "CREATE TABLE podpolye.depots(\n    depot_id   integer PRIMARY KEY,\n    depot_name varchar(40) NOT NULL,\n    sector     char(1) NOT NULL,\n    capacity_t integer)", "ALTER TABLE podpolye.depots ADD CONSTRAINT depots_sector_chk CHECK (sector IN (''A'',''B'',''C'',''D''))", "CREATE TABLE podpolye.sectors(sector char(1) PRIMARY KEY, title varchar(30) NOT NULL)", "INSERT INTO podpolye.sectors VALUES (''A'',''Заречный''),(''B'',''Вокзальный''),(''C'',''Старый город''),(''D'',''Фабричный'')", "ALTER TABLE podpolye.depots ADD CONSTRAINT depots_sector_fk FOREIGN KEY (sector) REFERENCES podpolye.sectors(sector) ON DELETE RESTRICT", "INSERT INTO podpolye.depots VALUES (1,''Арсенал №1'',''A'',800),(2,''Топливный склад'',''A'',450),(3,''Продовольственный'',''B'',300)", "CREATE TABLE podpolye.movements(\n    move_id  integer PRIMARY KEY,\n    depot_id integer NOT NULL REFERENCES podpolye.depots(depot_id) ON DELETE CASCADE,\n    at_date  date NOT NULL DEFAULT current_date,\n    tons     integer)", "INSERT INTO podpolye.movements(move_id, depot_id, at_date, tons) VALUES (1,1,''1944-09-11'',60),(2,1,''1944-09-15'',38),(3,2,''1944-09-12'',52),(4,3,''1944-09-14'',22),(5,3,''1944-09-18'',45)"], "expect": [{"args": {"table": "podpolye.movements"}, "probe": "indexes", "title": "индексы рейсов, кроме первичного ключа", "value": [["depot_id", false, "btree", false]]}, {"args": {"table": "podpolye.movements"}, "probe": "primary_key", "title": "первичный ключ не тронут", "value": ["move_id"]}, {"args": {"table": "podpolye.movements", "columns": ["move_id", "depot_id", "tons"], "order_by": "move_id"}, "probe": "rows", "title": "рейсы на месте", "value": [[1, 1, 60], [2, 1, 38], [3, 2, 52], [4, 3, 22], [5, 3, 45]]}], "reveal": "Что проверяется: индексы рейсов, кроме первичного ключа; первичный ключ не тронут; рейсы на месте."}', '{ddl,index}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (93, 3, 10, 'Сводка одним словом', 'Семён требует, чтобы сводка вывоза по секторам собиралась сама, одним словом. Мелкие рейсы до 30 тонн — текучка гарнизона, в сводку они не идут.

Создайте представление podpolye.depot_load, явно объявив его столбцы: sector — сектор склада и tons — суммарный вывоз по этому сектору. Учитывайте только рейсы тяжелее 30 тонн, записав условие отбора именно как tons > 30. Имена столбцов укажите в скобках после имени представления: CREATE VIEW podpolye.depot_load(sector, tons) AS ...', 'Представление — это сохранённый запрос: CREATE VIEW <имя>(<столбцы>) AS SELECT ... Внутри — соединение depots и movements по depot_id, отбор WHERE tons > 30 и группировка по сектору с sum(tons).', 'CREATE VIEW podpolye.depot_load(sector, tons) AS SELECT d.sector, sum(m.tons) FROM podpolye.depots d JOIN podpolye.movements m ON m.depot_id = d.depot_id WHERE m.tons > 30 GROUP BY d.sector', '{"mode": "model", "setup": ["CREATE SCHEMA podpolye", "CREATE TABLE podpolye.depots(\n    depot_id   integer PRIMARY KEY,\n    depot_name varchar(40) NOT NULL,\n    sector     char(1) NOT NULL,\n    capacity_t integer)", "ALTER TABLE podpolye.depots ADD CONSTRAINT depots_sector_chk CHECK (sector IN (''A'',''B'',''C'',''D''))", "CREATE TABLE podpolye.sectors(sector char(1) PRIMARY KEY, title varchar(30) NOT NULL)", "INSERT INTO podpolye.sectors VALUES (''A'',''Заречный''),(''B'',''Вокзальный''),(''C'',''Старый город''),(''D'',''Фабричный'')", "ALTER TABLE podpolye.depots ADD CONSTRAINT depots_sector_fk FOREIGN KEY (sector) REFERENCES podpolye.sectors(sector) ON DELETE RESTRICT", "INSERT INTO podpolye.depots VALUES (1,''Арсенал №1'',''A'',800),(2,''Топливный склад'',''A'',450),(3,''Продовольственный'',''B'',300)", "CREATE TABLE podpolye.movements(\n    move_id  integer PRIMARY KEY,\n    depot_id integer NOT NULL REFERENCES podpolye.depots(depot_id) ON DELETE CASCADE,\n    at_date  date NOT NULL DEFAULT current_date,\n    tons     integer)", "INSERT INTO podpolye.movements(move_id, depot_id, at_date, tons) VALUES (1,1,''1944-09-11'',60),(2,1,''1944-09-15'',38),(3,2,''1944-09-12'',52),(4,3,''1944-09-14'',22),(5,3,''1944-09-18'',45)"], "expect": [{"args": {"name": "podpolye.depot_load"}, "probe": "view_columns", "title": "столбцы представления", "value": ["sector", "tons"]}, {"args": {"name": "podpolye.depot_load", "mentions": ["depots", "movements", "sum", "group", "sector", "30"]}, "probe": "view_shape", "title": "форма определения представления", "value": [["существует", true], ["упоминает depots", true], ["упоминает movements", true], ["упоминает sum", true], ["упоминает group", true], ["упоминает sector", true], ["упоминает 30", true]]}], "reveal": "Что проверяется: столбцы представления; форма определения представления."}', '{ddl,view,select,where}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (94, 3, 11, 'Наблюдение за складами', 'За каждым складом закреплён свой человек. Один наблюдатель ведёт несколько складов, за одним складом могут следить двое — но пара «человек и склад» должна встречаться ровно один раз. Ключ здесь — именно пара.

Создайте таблицу podpolye.watch: spotter — строка не длиннее 20 символов; depot_id — целое, ссылающееся на podpolye.depots(depot_id). Первичный ключ должен быть составным: пара (spotter, depot_id).', 'Составной ключ нельзя объявить в одном столбце — он записывается отдельным элементом таблицы: PRIMARY KEY (spotter, depot_id). Ссылка на склады при этом остаётся обычным REFERENCES в определении depot_id.', 'CREATE TABLE podpolye.watch(spotter varchar(20), depot_id integer REFERENCES podpolye.depots(depot_id), PRIMARY KEY (spotter, depot_id))', '{"mode": "model", "post": ["INSERT INTO podpolye.watch VALUES (''Гриша'', 1)"], "setup": ["CREATE SCHEMA podpolye", "CREATE TABLE podpolye.depots(\n    depot_id   integer PRIMARY KEY,\n    depot_name varchar(40) NOT NULL,\n    sector     char(1) NOT NULL,\n    capacity_t integer)", "ALTER TABLE podpolye.depots ADD CONSTRAINT depots_sector_chk CHECK (sector IN (''A'',''B'',''C'',''D''))", "CREATE TABLE podpolye.sectors(sector char(1) PRIMARY KEY, title varchar(30) NOT NULL)", "INSERT INTO podpolye.sectors VALUES (''A'',''Заречный''),(''B'',''Вокзальный''),(''C'',''Старый город''),(''D'',''Фабричный'')", "ALTER TABLE podpolye.depots ADD CONSTRAINT depots_sector_fk FOREIGN KEY (sector) REFERENCES podpolye.sectors(sector) ON DELETE RESTRICT", "INSERT INTO podpolye.depots VALUES (1,''Арсенал №1'',''A'',800),(2,''Топливный склад'',''A'',450),(3,''Продовольственный'',''B'',300)"], "expect": [{"args": {"table": "podpolye.watch"}, "probe": "primary_key", "title": "состав первичного ключа наблюдения", "value": ["spotter", "depot_id"]}, {"args": {"table": "podpolye.watch"}, "probe": "columns", "title": "столбцы наблюдения", "value": [["spotter", "character varying", 20, true, false], ["depot_id", "integer", null, true, false]]}, {"args": {"table": "podpolye.watch"}, "probe": "foreign_keys", "title": "ссылка на склады", "value": [["depot_id", "podpolye.depots", "depot_id", "запрещает удаление"]]}, {"args": {"cases": [{"row": {"spotter": "Гриша", "depot_id": 1}, "label": "та же пара"}, {"row": {"spotter": "Гриша", "depot_id": 2}, "label": "другой склад"}, {"row": {"spotter": "Гриша", "depot_id": 77}, "label": "несуществующий склад"}], "table": "podpolye.watch"}, "probe": "accepts", "title": "повтор пары и другая пара", "value": [["та же пара", false], ["другой склад", true], ["несуществующий склад", false]]}], "reveal": "Что проверяется: состав первичного ключа наблюдения; столбцы наблюдения; ссылка на склады; повтор пары и другая пара."}', '{ddl,table,primary_key,foreign_key}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (95, 3, 12, 'Журнал радиограмм', 'Повтор донесения Центр считает подтверждением и удваивает оценку сил противника — одинаковых текстов быть не должно. Время отправки база ставит сама: радист в эфире на часы не смотрит.

Создайте таблицу podpolye.radiograms: radio_id — целое, первичный ключ; body — текст, обязательный, причём два донесения с одинаковым текстом в журнал попадать не должны; sent_at — отметка времени, обязательная, по умолчанию текущий момент.', '«Одинаковых текстов быть не должно» — это ограничение UNIQUE на столбце body. «Отметка времени» — тип timestamp, а текущий момент по умолчанию — DEFAULT now().', 'CREATE TABLE podpolye.radiograms(radio_id integer PRIMARY KEY, body text NOT NULL UNIQUE, sent_at timestamp NOT NULL DEFAULT now())', '{"mode": "model", "post": ["INSERT INTO podpolye.radiograms(radio_id, body) VALUES (1, ''связь установлена'')"], "setup": ["CREATE SCHEMA podpolye"], "expect": [{"args": {"table": "podpolye.radiograms"}, "probe": "columns", "title": "столбцы журнала донесений", "value": [["radio_id", "integer", null, true, false], ["body", "text", null, true, false], ["sent_at", "timestamp without time zone", null, true, true]]}, {"args": {"table": "podpolye.radiograms"}, "probe": "primary_key", "title": "первичный ключ журнала", "value": ["radio_id"]}, {"args": {"table": "podpolye.radiograms"}, "probe": "uniques", "title": "уникальность в журнале", "value": ["body"]}, {"args": {"table": "podpolye.radiograms", "columns": ["sent_at"]}, "probe": "default_kind", "title": "время проставляется само", "value": [["sent_at", "текущий момент"]]}, {"args": {"table": "podpolye.radiograms", "column": "sent_at"}, "probe": "rows_filled", "title": "отметка времени заполнена", "value": true}, {"args": {"cases": [{"row": {"body": "связь установлена", "radio_id": 2}, "label": "повтор текста"}, {"row": {"body": "иное донесение", "radio_id": 1}, "label": "повтор номера"}, {"row": {"body": "эшелон на восток", "radio_id": 2}, "label": "новое"}], "table": "podpolye.radiograms"}, "probe": "accepts", "title": "повтор текста, повтор номера и новое донесение", "value": [["повтор текста", false], ["повтор номера", false], ["новое", true]]}], "reveal": "Что проверяется: столбцы журнала донесений; первичный ключ журнала; уникальность в журнале; время проставляется само; отметка времени заполнена; повтор текста, повтор номера и новое донесение."}', '{ddl,table,unique,default}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (96, 4, 1, 'Роли отряда', 'Условное имя явки всплыло в немецкой сводке, а работали до сих пор все под одной учётной записью. Разграничение начинается с ролей: командование, разведка, агентура. Это группы, а не люди — входить под ними нельзя.

Заведите три роли: commanders, scouts и spies. Входить в систему непосредственно под ними нельзя.', 'Роль заводится оператором CREATE ROLE <имя> — по одному на каждую. Право входа по умолчанию выключено, поэтому дописывать ничего не нужно; главное — не написать CREATE USER, который как раз вход разрешает.', 'CREATE ROLE commanders; CREATE ROLE scouts; CREATE ROLE spies', '{"mode": "model", "setup": ["CREATE SCHEMA podpolye", "CREATE TABLE podpolye.depots(\n    depot_id   integer PRIMARY KEY,\n    depot_name varchar(40) NOT NULL,\n    sector     char(1) NOT NULL,\n    capacity_t integer)", "INSERT INTO podpolye.depots VALUES (1,''Арсенал №1'',''A'',800),(2,''Топливный склад'',''A'',450),(3,''Продовольственный'',''B'',300)", "CREATE TABLE podpolye.safehouses(\n    house_id  integer PRIMARY KEY,\n    code_name varchar(20) NOT NULL,\n    street    varchar(40) NOT NULL,\n    keeper    varchar(20) NOT NULL,\n    sector    char(1) NOT NULL,\n    is_burnt  boolean NOT NULL DEFAULT false)", "INSERT INTO podpolye.safehouses VALUES (1,''Мельница'',''Заречная, 7'',''Прохор'',''A'',false),(2,''Аптека'',''Соборная, 14'',''Вера'',''A'',true),(3,''Сапожник'',''Кузнечная, 3'',''Пётр'',''B'',false),(4,''Пекарня'',''Хлебный пер., 2'',''Дарья'',''B'',false),(5,''Часовщик'',''Ратушная, 21'',''Артур'',''C'',true),(6,''Прачечная'',''Луговая, 9'',''Клава'',''C'',false)"], "expect": [{"args": {"names": ["commanders", "scouts", "spies"]}, "probe": "roles", "title": "роли отряда", "value": [["commanders", false, false], ["scouts", false, false], ["spies", false, false]]}, {"args": {}, "probe": "all_roles", "title": "посторонних ролей не заведено", "value": ["commanders", "scouts", "spies"]}, {"args": {}, "probe": "all_memberships", "title": "роли друг в друга не вложены", "value": []}], "reveal": "Что проверяется: роли отряда; посторонних ролей не заведено; роли друг в друга не вложены."}', '{dcl,role}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (97, 4, 2, 'Полный доступ командованию', 'Семён отвечает за отряд целиком; урезать его в правах бессмысленно — он возьмёт их обратно окольным путём. Полный доступ начинается с права войти в саму схему.

Откройте командованию полный доступ: роль commanders должна получить право пользоваться схемой podpolye и все привилегии на таблицы podpolye.depots и podpolye.safehouses.', 'Право войти в схему и права на таблицы выдаются разными операторами: GRANT USAGE ON SCHEMA podpolye TO commanders и GRANT ALL PRIVILEGES ON <таблицы> TO commanders. Слово ALL PRIVILEGES заменяет перечисление всех прав, а таблицы можно указать через запятую.', 'GRANT USAGE ON SCHEMA podpolye TO commanders; GRANT ALL PRIVILEGES ON podpolye.depots, podpolye.safehouses TO commanders', '{"mode": "model", "setup": ["CREATE SCHEMA podpolye", "CREATE TABLE podpolye.depots(\n    depot_id   integer PRIMARY KEY,\n    depot_name varchar(40) NOT NULL,\n    sector     char(1) NOT NULL,\n    capacity_t integer)", "INSERT INTO podpolye.depots VALUES (1,''Арсенал №1'',''A'',800),(2,''Топливный склад'',''A'',450),(3,''Продовольственный'',''B'',300)", "CREATE TABLE podpolye.safehouses(\n    house_id  integer PRIMARY KEY,\n    code_name varchar(20) NOT NULL,\n    street    varchar(40) NOT NULL,\n    keeper    varchar(20) NOT NULL,\n    sector    char(1) NOT NULL,\n    is_burnt  boolean NOT NULL DEFAULT false)", "INSERT INTO podpolye.safehouses VALUES (1,''Мельница'',''Заречная, 7'',''Прохор'',''A'',false),(2,''Аптека'',''Соборная, 14'',''Вера'',''A'',true),(3,''Сапожник'',''Кузнечная, 3'',''Пётр'',''B'',false),(4,''Пекарня'',''Хлебный пер., 2'',''Дарья'',''B'',false),(5,''Часовщик'',''Ратушная, 21'',''Артур'',''C'',true),(6,''Прачечная'',''Луговая, 9'',''Клава'',''C'',false)", "CREATE ROLE commanders", "CREATE ROLE scouts", "CREATE ROLE spies"], "expect": [{"args": {"schema": "podpolye", "grantee": "commanders"}, "probe": "schema_privs", "title": "права командования на схему", "value": ["USAGE"]}, {"args": {"privs": ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"], "table": "podpolye.depots", "grantee": "commanders"}, "probe": "has_privs", "title": "права командования на склады", "value": [["SELECT", true], ["INSERT", true], ["UPDATE", true], ["DELETE", true], ["TRUNCATE", true], ["REFERENCES", true], ["TRIGGER", true]]}, {"args": {"privs": ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"], "table": "podpolye.safehouses", "grantee": "commanders"}, "probe": "has_privs", "title": "права командования на явки", "value": [["SELECT", true], ["INSERT", true], ["UPDATE", true], ["DELETE", true], ["TRUNCATE", true], ["REFERENCES", true], ["TRIGGER", true]]}, {"args": {"table": "podpolye.safehouses", "grantee": "commanders"}, "probe": "grantable", "title": "передоверия не давали", "value": [["DELETE", false], ["INSERT", false], ["REFERENCES", false], ["SELECT", false], ["TRIGGER", false], ["TRUNCATE", false], ["UPDATE", false]]}, {"args": {"privs": ["SELECT", "UPDATE"], "table": "podpolye.safehouses", "grantees": ["scouts", "spies", "PUBLIC"]}, "probe": "privs_matrix", "title": "остальным ничего не открыли", "value": [["scouts", "SELECT", false], ["scouts", "UPDATE", false], ["spies", "SELECT", false], ["spies", "UPDATE", false], ["PUBLIC", "SELECT", false], ["PUBLIC", "UPDATE", false]]}], "reveal": "Что проверяется: права командования на схему; права командования на склады; права командования на явки; передоверия не давали; остальным ничего не открыли."}', '{dcl,grant}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (98, 4, 3, 'Разведке — только перо', 'Разведчику нужно одно: принести новое. Увидел эшелон — вписал строку. Право править и стирать чужие записи в руках противника опаснее, чем право читать: тихо изменённые координаты уведут удар в жилой квартал.

Выдайте роли scouts право пользоваться схемой podpolye и на таблицу podpolye.depots — только чтение и добавление строк. Права изменять и удалять записи у неё быть не должно.', 'Права перечисляются через запятую в одном операторе: GRANT SELECT, INSERT ON podpolye.depots TO scouts. Отдельным оператором — доступ к схеме: GRANT USAGE ON SCHEMA podpolye TO scouts. ALL здесь писать нельзя — это выдаст лишнее.', 'GRANT USAGE ON SCHEMA podpolye TO scouts; GRANT SELECT, INSERT ON podpolye.depots TO scouts', '{"mode": "model", "setup": ["CREATE SCHEMA podpolye", "CREATE TABLE podpolye.depots(\n    depot_id   integer PRIMARY KEY,\n    depot_name varchar(40) NOT NULL,\n    sector     char(1) NOT NULL,\n    capacity_t integer)", "INSERT INTO podpolye.depots VALUES (1,''Арсенал №1'',''A'',800),(2,''Топливный склад'',''A'',450),(3,''Продовольственный'',''B'',300)", "CREATE TABLE podpolye.safehouses(\n    house_id  integer PRIMARY KEY,\n    code_name varchar(20) NOT NULL,\n    street    varchar(40) NOT NULL,\n    keeper    varchar(20) NOT NULL,\n    sector    char(1) NOT NULL,\n    is_burnt  boolean NOT NULL DEFAULT false)", "INSERT INTO podpolye.safehouses VALUES (1,''Мельница'',''Заречная, 7'',''Прохор'',''A'',false),(2,''Аптека'',''Соборная, 14'',''Вера'',''A'',true),(3,''Сапожник'',''Кузнечная, 3'',''Пётр'',''B'',false),(4,''Пекарня'',''Хлебный пер., 2'',''Дарья'',''B'',false),(5,''Часовщик'',''Ратушная, 21'',''Артур'',''C'',true),(6,''Прачечная'',''Луговая, 9'',''Клава'',''C'',false)", "CREATE ROLE commanders", "CREATE ROLE scouts", "CREATE ROLE spies", "GRANT USAGE ON SCHEMA podpolye TO commanders", "GRANT ALL PRIVILEGES ON podpolye.depots, podpolye.safehouses TO commanders"], "expect": [{"args": {"schema": "podpolye", "grantee": "scouts"}, "probe": "schema_privs", "title": "права разведки на схему", "value": ["USAGE"]}, {"args": {"privs": ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"], "table": "podpolye.depots", "grantee": "scouts"}, "probe": "has_privs", "title": "права разведки на склады", "value": [["SELECT", true], ["INSERT", true], ["UPDATE", false], ["DELETE", false], ["TRUNCATE", false], ["REFERENCES", false], ["TRIGGER", false]]}, {"args": {"table": "podpolye.depots", "grantee": "scouts"}, "probe": "grantable", "title": "передоверия не давали", "value": [["INSERT", false], ["SELECT", false]]}, {"args": {"privs": ["SELECT"], "table": "podpolye.depots", "grantees": ["spies", "PUBLIC"]}, "probe": "privs_matrix", "title": "остальным складов не открывали", "value": [["spies", "SELECT", false], ["PUBLIC", "SELECT", false]]}, {"args": {}, "probe": "all_memberships", "title": "роли друг в друга не вложены", "value": []}, {"args": {"schema": "podpolye"}, "probe": "default_privs", "title": "прав по умолчанию не заводили", "value": []}], "reveal": "Что проверяется: права разведки на схему; права разведки на склады; передоверия не давали; остальным складов не открывали; роли друг в друга не вложены; прав по умолчанию не заводили."}', '{dcl,grant}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (99, 4, 4, 'Явки по столбцам', 'В ночь спешки агентам открыли таблицу явок целиком: адреса, хозяева, всё. Агенту нужны только номер явки и сектор; улица и хозяин не должны быть доступны ему ни при каких условиях. Сначала отобрать всё — потом вернуть ровно необходимое.

Отберите у роли spies все права на таблицу podpolye.safehouses, а затем выдайте ей право читать только два столбца — house_id и sector.', 'Сначала REVOKE ALL ON podpolye.safehouses FROM spies. Права на отдельные столбцы выдаются перечислением в скобках сразу после названия права: GRANT SELECT (house_id, sector) ON podpolye.safehouses TO spies.', 'REVOKE ALL ON podpolye.safehouses FROM spies; GRANT SELECT (house_id, sector) ON podpolye.safehouses TO spies', '{"mode": "model", "setup": ["CREATE SCHEMA podpolye", "CREATE TABLE podpolye.depots(\n    depot_id   integer PRIMARY KEY,\n    depot_name varchar(40) NOT NULL,\n    sector     char(1) NOT NULL,\n    capacity_t integer)", "INSERT INTO podpolye.depots VALUES (1,''Арсенал №1'',''A'',800),(2,''Топливный склад'',''A'',450),(3,''Продовольственный'',''B'',300)", "CREATE TABLE podpolye.safehouses(\n    house_id  integer PRIMARY KEY,\n    code_name varchar(20) NOT NULL,\n    street    varchar(40) NOT NULL,\n    keeper    varchar(20) NOT NULL,\n    sector    char(1) NOT NULL,\n    is_burnt  boolean NOT NULL DEFAULT false)", "INSERT INTO podpolye.safehouses VALUES (1,''Мельница'',''Заречная, 7'',''Прохор'',''A'',false),(2,''Аптека'',''Соборная, 14'',''Вера'',''A'',true),(3,''Сапожник'',''Кузнечная, 3'',''Пётр'',''B'',false),(4,''Пекарня'',''Хлебный пер., 2'',''Дарья'',''B'',false),(5,''Часовщик'',''Ратушная, 21'',''Артур'',''C'',true),(6,''Прачечная'',''Луговая, 9'',''Клава'',''C'',false)", "CREATE ROLE commanders", "CREATE ROLE scouts", "CREATE ROLE spies", "GRANT USAGE ON SCHEMA podpolye TO commanders", "GRANT ALL PRIVILEGES ON podpolye.depots, podpolye.safehouses TO commanders", "GRANT USAGE ON SCHEMA podpolye TO scouts", "GRANT SELECT, INSERT ON podpolye.depots TO scouts", "GRANT USAGE ON SCHEMA podpolye TO spies", "GRANT SELECT ON podpolye.safehouses TO spies"], "expect": [{"args": {"privs": ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"], "table": "podpolye.safehouses", "grantee": "spies"}, "probe": "has_privs", "title": "права на таблицу явок целиком", "value": [["SELECT", false], ["INSERT", false], ["UPDATE", false], ["DELETE", false], ["TRUNCATE", false], ["REFERENCES", false], ["TRIGGER", false]]}, {"args": {"table": "podpolye.safehouses", "grantee": "spies"}, "probe": "column_grants_all", "title": "права на отдельные столбцы", "value": [["house_id", "SELECT", false], ["sector", "SELECT", false]]}, {"args": {"table": "podpolye.safehouses", "columns": ["house_id", "sector", "street", "keeper"], "grantee": "spies"}, "probe": "can_read_columns", "title": "что агент может прочитать", "value": [["house_id", true], ["sector", true], ["street", false], ["keeper", false]]}, {"args": {"table": "podpolye.safehouses", "grantee": "spies"}, "probe": "grantable", "title": "передоверия не давали", "value": []}, {"args": {"privs": ["SELECT"], "table": "podpolye.safehouses", "grantees": ["scouts", "PUBLIC"]}, "probe": "privs_matrix", "title": "посторонним явки не открывали", "value": [["scouts", "SELECT", false], ["PUBLIC", "SELECT", false]]}, {"args": {"schema": "podpolye"}, "probe": "default_privs", "title": "прав по умолчанию не заводили", "value": []}], "reveal": "Что проверяется: права на таблицу явок целиком; права на отдельные столбцы; что агент может прочитать; передоверия не давали; посторонним явки не открывали; прав по умолчанию не заводили."}', '{dcl,revoke,column_privileges}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (100, 4, 5, 'Явки по строкам', 'Вторая линия обороны: проваленная явка опаснее незнания — агент придёт по адресу, который уже под наблюдением. Строки с провалом должны исчезнуть из его выборки на уровне правила самой таблицы.

Включите на таблице podpolye.safehouses защиту строк и создайте политику с именем house_open, разрешающую роли spies читать только те строки, где is_burnt равно false.', 'Защита строк включается отдельным оператором: ALTER TABLE ... ENABLE ROW LEVEL SECURITY. Правило видимости — политикой: CREATE POLICY house_open ON podpolye.safehouses FOR SELECT TO spies USING (is_burnt = false). Пока защита не включена, политика не действует.', 'ALTER TABLE podpolye.safehouses ENABLE ROW LEVEL SECURITY; CREATE POLICY house_open ON podpolye.safehouses FOR SELECT TO spies USING (is_burnt = false)', '{"mode": "model", "post": ["INSERT INTO podpolye.safehouses VALUES (7,''Мост'',''Речная, 4'',''Игнат'',''D'',false),(8,''Склеп'',''Тихая, 1'',''Ким'',''D'',true)"], "setup": ["CREATE SCHEMA podpolye", "CREATE TABLE podpolye.depots(\n    depot_id   integer PRIMARY KEY,\n    depot_name varchar(40) NOT NULL,\n    sector     char(1) NOT NULL,\n    capacity_t integer)", "INSERT INTO podpolye.depots VALUES (1,''Арсенал №1'',''A'',800),(2,''Топливный склад'',''A'',450),(3,''Продовольственный'',''B'',300)", "CREATE TABLE podpolye.safehouses(\n    house_id  integer PRIMARY KEY,\n    code_name varchar(20) NOT NULL,\n    street    varchar(40) NOT NULL,\n    keeper    varchar(20) NOT NULL,\n    sector    char(1) NOT NULL,\n    is_burnt  boolean NOT NULL DEFAULT false)", "INSERT INTO podpolye.safehouses VALUES (1,''Мельница'',''Заречная, 7'',''Прохор'',''A'',false),(2,''Аптека'',''Соборная, 14'',''Вера'',''A'',true),(3,''Сапожник'',''Кузнечная, 3'',''Пётр'',''B'',false),(4,''Пекарня'',''Хлебный пер., 2'',''Дарья'',''B'',false),(5,''Часовщик'',''Ратушная, 21'',''Артур'',''C'',true),(6,''Прачечная'',''Луговая, 9'',''Клава'',''C'',false)", "CREATE ROLE commanders", "CREATE ROLE scouts", "CREATE ROLE spies", "GRANT USAGE ON SCHEMA podpolye TO commanders", "GRANT ALL PRIVILEGES ON podpolye.depots, podpolye.safehouses TO commanders", "GRANT USAGE ON SCHEMA podpolye TO scouts", "GRANT SELECT, INSERT ON podpolye.depots TO scouts", "GRANT USAGE ON SCHEMA podpolye TO spies", "GRANT SELECT (house_id, sector) ON podpolye.safehouses TO spies"], "expect": [{"args": {"table": "podpolye.safehouses"}, "probe": "rls", "title": "защита строк на таблице явок", "value": [true, false]}, {"args": {"table": "podpolye.safehouses"}, "probe": "policies", "title": "политика", "value": [["house_open", "SELECT", "spies"]]}, {"args": {"role": "spies", "table": "podpolye.safehouses", "columns": ["house_id"], "order_by": "house_id"}, "probe": "visible_rows", "title": "номера явок, видимых агенту", "value": [[1], [3], [4], [6], [7]]}, {"args": {"privs": ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"], "table": "podpolye.safehouses", "grantee": "spies"}, "probe": "has_privs", "title": "лишних прав агенту не выдали", "value": [["SELECT", false], ["INSERT", false], ["UPDATE", false], ["DELETE", false], ["TRUNCATE", false], ["REFERENCES", false], ["TRIGGER", false]]}, {"args": {"table": "podpolye.safehouses", "grantee": "spies"}, "probe": "column_grants_all", "title": "столбцовые права не расширяли", "value": [["house_id", "SELECT", false], ["sector", "SELECT", false]]}], "reveal": "Что проверяется: защита строк на таблице явок; политика; номера явок, видимых агенту; лишних прав агенту не выдали; столбцовые права не расширяли."}', '{dcl,rls,policy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (101, 4, 6, 'Боец Гриша', 'Пора заводить людей поимённо. Если Гришу возьмут, отключить надо будет именно его, не тронув остальных. Личных прав не выдавать ни одного: боец получает их только через роль.

Заведите учётную запись grisha, которая может входить в систему, и включите её в роль scouts. Никаких прав на таблицы непосредственно этой учётной записи выдавать не нужно.', 'Учётная запись с правом входа — CREATE ROLE grisha LOGIN (или CREATE USER grisha). Включение в роль — тем же словом, что и выдача прав: GRANT scouts TO grisha. На таблицы при этом не выдаётся ничего.', 'CREATE ROLE grisha LOGIN; GRANT scouts TO grisha', '{"mode": "model", "setup": ["CREATE SCHEMA podpolye", "CREATE TABLE podpolye.depots(\n    depot_id   integer PRIMARY KEY,\n    depot_name varchar(40) NOT NULL,\n    sector     char(1) NOT NULL,\n    capacity_t integer)", "INSERT INTO podpolye.depots VALUES (1,''Арсенал №1'',''A'',800),(2,''Топливный склад'',''A'',450),(3,''Продовольственный'',''B'',300)", "CREATE TABLE podpolye.safehouses(\n    house_id  integer PRIMARY KEY,\n    code_name varchar(20) NOT NULL,\n    street    varchar(40) NOT NULL,\n    keeper    varchar(20) NOT NULL,\n    sector    char(1) NOT NULL,\n    is_burnt  boolean NOT NULL DEFAULT false)", "INSERT INTO podpolye.safehouses VALUES (1,''Мельница'',''Заречная, 7'',''Прохор'',''A'',false),(2,''Аптека'',''Соборная, 14'',''Вера'',''A'',true),(3,''Сапожник'',''Кузнечная, 3'',''Пётр'',''B'',false),(4,''Пекарня'',''Хлебный пер., 2'',''Дарья'',''B'',false),(5,''Часовщик'',''Ратушная, 21'',''Артур'',''C'',true),(6,''Прачечная'',''Луговая, 9'',''Клава'',''C'',false)", "CREATE ROLE commanders", "CREATE ROLE scouts", "CREATE ROLE spies", "GRANT USAGE ON SCHEMA podpolye TO commanders", "GRANT ALL PRIVILEGES ON podpolye.depots, podpolye.safehouses TO commanders", "GRANT USAGE ON SCHEMA podpolye TO scouts", "GRANT SELECT, INSERT ON podpolye.depots TO scouts", "GRANT USAGE ON SCHEMA podpolye TO spies", "GRANT SELECT (house_id, sector) ON podpolye.safehouses TO spies", "ALTER TABLE podpolye.safehouses ENABLE ROW LEVEL SECURITY", "CREATE POLICY house_open ON podpolye.safehouses FOR SELECT TO spies USING (is_burnt = false)"], "expect": [{"args": {"names": ["grisha"]}, "probe": "roles", "title": "учётная запись бойца", "value": [["grisha", true, false]]}, {"args": {"member": "grisha"}, "probe": "member_of", "title": "в какие роли включён боец", "value": ["scouts"]}, {"args": {"member": "grisha"}, "probe": "member_admin", "title": "раздавать членство боец не может", "value": [["scouts", false]]}, {"args": {"table": "podpolye.depots", "grantee": "grisha"}, "probe": "direct_table_grants", "title": "личных прав на таблицы нет", "value": []}, {"args": {"table": "podpolye.depots", "grantee": "grisha"}, "probe": "column_grants_all", "title": "личных прав на столбцы нет", "value": []}, {"args": {"privs": ["SELECT", "INSERT"], "table": "podpolye.depots", "grantee": "grisha"}, "probe": "has_privs", "title": "права пришли через роль", "value": [["SELECT", true], ["INSERT", true]]}, {"args": {"table": "podpolye.depots"}, "probe": "public_privs", "title": "посторонним ничего не открыли", "value": []}, {"args": {"schema": "podpolye"}, "probe": "default_privs", "title": "прав по умолчанию не заводили", "value": []}], "reveal": "Что проверяется: учётная запись бойца; в какие роли включён боец; раздавать членство боец не может; личных прав на таблицы нет; личных прав на столбцы нет; права пришли через роль; посторонним ничего не открыли; прав по умолчанию не заводили."}', '{dcl,role,membership}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (102, 4, 7, 'Отзыв у PUBLIC', 'Права на таблицу явок в спешке выдали PUBLIC — всем, кто сумеет подключиться. Вот почему имя явки оказалось в немецкой сводке: взламывать ничего не пришлось.

Отберите у PUBLIC все права на таблицу podpolye.safehouses. Права, выданные роли commanders отдельно, при этом трогать нельзя.', 'PUBLIC в операторе отзыва пишется как обычное имя роли: REVOKE ALL ON podpolye.safehouses FROM PUBLIC. Отзыв у PUBLIC не трогает права, выданные ролям поимённо, — их отбирать не нужно.', 'REVOKE ALL ON podpolye.safehouses FROM PUBLIC', '{"mode": "model", "setup": ["CREATE SCHEMA podpolye", "CREATE TABLE podpolye.depots(\n    depot_id   integer PRIMARY KEY,\n    depot_name varchar(40) NOT NULL,\n    sector     char(1) NOT NULL,\n    capacity_t integer)", "INSERT INTO podpolye.depots VALUES (1,''Арсенал №1'',''A'',800),(2,''Топливный склад'',''A'',450),(3,''Продовольственный'',''B'',300)", "CREATE TABLE podpolye.safehouses(\n    house_id  integer PRIMARY KEY,\n    code_name varchar(20) NOT NULL,\n    street    varchar(40) NOT NULL,\n    keeper    varchar(20) NOT NULL,\n    sector    char(1) NOT NULL,\n    is_burnt  boolean NOT NULL DEFAULT false)", "INSERT INTO podpolye.safehouses VALUES (1,''Мельница'',''Заречная, 7'',''Прохор'',''A'',false),(2,''Аптека'',''Соборная, 14'',''Вера'',''A'',true),(3,''Сапожник'',''Кузнечная, 3'',''Пётр'',''B'',false),(4,''Пекарня'',''Хлебный пер., 2'',''Дарья'',''B'',false),(5,''Часовщик'',''Ратушная, 21'',''Артур'',''C'',true),(6,''Прачечная'',''Луговая, 9'',''Клава'',''C'',false)", "CREATE ROLE commanders", "CREATE ROLE scouts", "CREATE ROLE spies", "GRANT USAGE ON SCHEMA podpolye TO commanders", "GRANT ALL PRIVILEGES ON podpolye.depots, podpolye.safehouses TO commanders", "GRANT USAGE ON SCHEMA podpolye TO scouts", "GRANT SELECT, INSERT ON podpolye.depots TO scouts", "GRANT USAGE ON SCHEMA podpolye TO spies", "GRANT SELECT (house_id, sector) ON podpolye.safehouses TO spies", "ALTER TABLE podpolye.safehouses ENABLE ROW LEVEL SECURITY", "CREATE POLICY house_open ON podpolye.safehouses FOR SELECT TO spies USING (is_burnt = false)", "CREATE ROLE grisha LOGIN", "GRANT scouts TO grisha", "GRANT SELECT ON podpolye.safehouses TO PUBLIC"], "expect": [{"args": {"table": "podpolye.safehouses"}, "probe": "public_privs", "title": "права PUBLIC на явки", "value": []}, {"args": {"privs": ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"], "table": "podpolye.safehouses", "grantee": "commanders"}, "probe": "has_privs", "title": "права командования не тронуты", "value": [["SELECT", true], ["INSERT", true], ["UPDATE", true], ["DELETE", true], ["TRUNCATE", true], ["REFERENCES", true], ["TRIGGER", true]]}, {"args": {"privs": ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"], "table": "podpolye.safehouses", "grantee": "spies"}, "probe": "has_privs", "title": "агентура сверх столбцов ничего не получила", "value": [["SELECT", false], ["INSERT", false], ["UPDATE", false], ["DELETE", false], ["TRUNCATE", false], ["REFERENCES", false], ["TRIGGER", false]]}, {"args": {"privs": ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"], "table": "podpolye.safehouses", "grantee": "scouts"}, "probe": "has_privs", "title": "разведке явки не открывали", "value": [["SELECT", false], ["INSERT", false], ["UPDATE", false], ["DELETE", false], ["TRUNCATE", false], ["REFERENCES", false], ["TRIGGER", false]]}, {"args": {"table": "podpolye.safehouses"}, "probe": "columns", "title": "таблица явок цела", "value": [["house_id", "integer", null, true, false], ["code_name", "character varying", 20, true, false], ["street", "character varying", 40, true, false], ["keeper", "character varying", 20, true, false], ["sector", "character", 1, true, false], ["is_burnt", "boolean", null, true, true]]}], "reveal": "Что проверяется: права PUBLIC на явки; права командования не тронуты; агентура сверх столбцов ничего не получила; разведке явки не открывали; таблица явок цела."}', '{dcl,revoke,public}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (103, 4, 8, 'Права наперёд', 'Каждая новая таблица появляется закрытой, и разведка узнаёт о ней, когда кто-нибудь вспомнит выдать права. Правило должно действовать наперёд: всё, что появится в схеме, разведка видит сразу.

Задайте право по умолчанию: все таблицы, которые впредь будут создаваться в схеме podpolye, должны становиться доступными роли scouts на чтение.', 'Права по умолчанию задаются оператором ALTER DEFAULT PRIVILEGES IN SCHEMA podpolye GRANT SELECT ON TABLES TO scouts. Он не трогает существующие таблицы, а описывает, что произойдёт с будущими.', 'ALTER DEFAULT PRIVILEGES IN SCHEMA podpolye GRANT SELECT ON TABLES TO scouts', '{"mode": "model", "post": ["CREATE TABLE podpolye.trains(train_id integer PRIMARY KEY, cargo_ru text)"], "setup": ["CREATE SCHEMA podpolye", "CREATE TABLE podpolye.depots(\n    depot_id   integer PRIMARY KEY,\n    depot_name varchar(40) NOT NULL,\n    sector     char(1) NOT NULL,\n    capacity_t integer)", "INSERT INTO podpolye.depots VALUES (1,''Арсенал №1'',''A'',800),(2,''Топливный склад'',''A'',450),(3,''Продовольственный'',''B'',300)", "CREATE TABLE podpolye.safehouses(\n    house_id  integer PRIMARY KEY,\n    code_name varchar(20) NOT NULL,\n    street    varchar(40) NOT NULL,\n    keeper    varchar(20) NOT NULL,\n    sector    char(1) NOT NULL,\n    is_burnt  boolean NOT NULL DEFAULT false)", "INSERT INTO podpolye.safehouses VALUES (1,''Мельница'',''Заречная, 7'',''Прохор'',''A'',false),(2,''Аптека'',''Соборная, 14'',''Вера'',''A'',true),(3,''Сапожник'',''Кузнечная, 3'',''Пётр'',''B'',false),(4,''Пекарня'',''Хлебный пер., 2'',''Дарья'',''B'',false),(5,''Часовщик'',''Ратушная, 21'',''Артур'',''C'',true),(6,''Прачечная'',''Луговая, 9'',''Клава'',''C'',false)", "CREATE ROLE commanders", "CREATE ROLE scouts", "CREATE ROLE spies", "GRANT USAGE ON SCHEMA podpolye TO commanders", "GRANT ALL PRIVILEGES ON podpolye.depots, podpolye.safehouses TO commanders", "GRANT USAGE ON SCHEMA podpolye TO scouts", "GRANT SELECT, INSERT ON podpolye.depots TO scouts", "GRANT USAGE ON SCHEMA podpolye TO spies", "GRANT SELECT (house_id, sector) ON podpolye.safehouses TO spies", "ALTER TABLE podpolye.safehouses ENABLE ROW LEVEL SECURITY", "CREATE POLICY house_open ON podpolye.safehouses FOR SELECT TO spies USING (is_burnt = false)", "CREATE ROLE grisha LOGIN", "GRANT scouts TO grisha"], "expect": [{"args": {"schema": "podpolye"}, "probe": "default_privs", "title": "правило по умолчанию в схеме подполья", "value": [["r", "scouts", "SELECT"]]}, {"args": {"schema": "public"}, "probe": "default_privs", "title": "в других схемах правил не заводили", "value": []}, {"args": {"privs": ["SELECT"], "table": "podpolye.trains", "grantee": "scouts"}, "probe": "has_privs", "title": "новая таблица сразу доступна разведке", "value": [["SELECT", true]]}, {"args": {"privs": ["SELECT"], "table": "podpolye.trains", "grantees": ["spies", "PUBLIC"]}, "probe": "privs_matrix", "title": "посторонним она недоступна", "value": [["spies", "SELECT", false], ["PUBLIC", "SELECT", false]]}, {"args": {"schema": "podpolye", "grantee": "scouts"}, "probe": "schema_privs", "title": "доступ разведки к схеме не тронут", "value": ["USAGE"]}, {"args": {}, "probe": "all_memberships", "title": "членство ролей не меняли", "value": [["grisha", "scouts"]]}], "reveal": "Что проверяется: правило по умолчанию в схеме подполья; в других схемах правил не заводили; новая таблица сразу доступна разведке; посторонним она недоступна; доступ разведки к схеме не тронут; членство ролей не меняли."}', '{dcl,default_privileges}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (105, 4, 10, 'Защита от владельца', 'Политика защиты строк не действует на владельца таблицы: тот, кто доберётся до учётной записи узла, увидит все явки разом. Правило надо сделать обязательным и для владельца — пусть узел, оставшись без хозяев, не выдаст никого.

Включите для таблицы podpolye.safehouses принудительную защиту строк, чтобы действующие политики распространялись и на владельца таблицы.', 'Принудительный режим включается оператором ALTER TABLE podpolye.safehouses FORCE ROW LEVEL SECURITY. Обычный ENABLE уже включён раньше — FORCE добавляется поверх него и распространяет правила на владельца.', 'ALTER TABLE podpolye.safehouses FORCE ROW LEVEL SECURITY', '{"mode": "model", "setup": ["CREATE SCHEMA podpolye", "CREATE TABLE podpolye.depots(\n    depot_id   integer PRIMARY KEY,\n    depot_name varchar(40) NOT NULL,\n    sector     char(1) NOT NULL,\n    capacity_t integer)", "INSERT INTO podpolye.depots VALUES (1,''Арсенал №1'',''A'',800),(2,''Топливный склад'',''A'',450),(3,''Продовольственный'',''B'',300)", "CREATE TABLE podpolye.safehouses(\n    house_id  integer PRIMARY KEY,\n    code_name varchar(20) NOT NULL,\n    street    varchar(40) NOT NULL,\n    keeper    varchar(20) NOT NULL,\n    sector    char(1) NOT NULL,\n    is_burnt  boolean NOT NULL DEFAULT false)", "INSERT INTO podpolye.safehouses VALUES (1,''Мельница'',''Заречная, 7'',''Прохор'',''A'',false),(2,''Аптека'',''Соборная, 14'',''Вера'',''A'',true),(3,''Сапожник'',''Кузнечная, 3'',''Пётр'',''B'',false),(4,''Пекарня'',''Хлебный пер., 2'',''Дарья'',''B'',false),(5,''Часовщик'',''Ратушная, 21'',''Артур'',''C'',true),(6,''Прачечная'',''Луговая, 9'',''Клава'',''C'',false)", "CREATE ROLE commanders", "CREATE ROLE scouts", "CREATE ROLE spies", "GRANT USAGE ON SCHEMA podpolye TO commanders", "GRANT ALL PRIVILEGES ON podpolye.depots, podpolye.safehouses TO commanders", "GRANT USAGE ON SCHEMA podpolye TO scouts", "GRANT SELECT, INSERT ON podpolye.depots TO scouts", "GRANT USAGE ON SCHEMA podpolye TO spies", "GRANT SELECT (house_id, sector) ON podpolye.safehouses TO spies", "ALTER TABLE podpolye.safehouses ENABLE ROW LEVEL SECURITY", "CREATE POLICY house_open ON podpolye.safehouses FOR SELECT TO spies USING (is_burnt = false)", "CREATE ROLE grisha LOGIN", "GRANT scouts TO grisha", "ALTER DEFAULT PRIVILEGES IN SCHEMA podpolye GRANT SELECT ON TABLES TO scouts", "GRANT SELECT ON podpolye.safehouses TO commanders WITH GRANT OPTION"], "expect": [{"args": {"table": "podpolye.safehouses"}, "probe": "rls", "title": "принудительная защита строк", "value": [true, true]}, {"args": {"table": "podpolye.safehouses"}, "probe": "policies", "title": "политика на месте", "value": [["house_open", "SELECT", "spies"]]}, {"args": {"role": "owner", "table": "podpolye.safehouses", "columns": ["house_id"], "order_by": "house_id"}, "probe": "visible_rows", "title": "владелец больше не видит ни одной явки", "value": []}, {"args": {"table": "podpolye.safehouses"}, "probe": "public_privs", "title": "посторонним прав не раздавали", "value": []}], "reveal": "Что проверяется: принудительная защита строк; политика на месте; владелец больше не видит ни одной явки; посторонним прав не раздавали."}', '{dcl,rls,force}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (14, 0, 13, 'Сила в единстве', 'Подсчитайте количество солдат в каждой воинской части и выведите названия этих частей. Названия частей выведите в алфавитном порядке. Это покажет, какие подразделения были наиболее многочисленными', 'Группировка по `unit_id` с использованием `COUNT(*)`', NULL, '{"data": [["1-й отдельный чехословацкий батальон", 2], ["1-й чехословацкий отдельный батальон", 1], ["1-я гвардейская танковая армия", 2], ["1-я морская бригада", 1], ["101-й инженерно-сапёрный батальон", 2], ["101-й полк НКВД", 1], ["101-й учебный полк", 1], ["106-я стрелковая дивизия", 1], ["14-я отдельная штрафная рота", 1], ["150-я стрелковая дивизия", 2], ["16-я воздушная армия", 2], ["18-я дивизия СС \"Хорст Вессель\"", 1], ["2-я ударная армия", 1], ["225-й отдельный инженерный батальон", 1], ["28-я дивизия народного ополчения", 1], ["3-я воздушная армия", 1], ["316-я стрелковая дивизия", 2], ["369-й отдельный батальон морской пехоты", 1], ["37-й гвардейский миномётный полк", 1], ["46-й гвардейский ночной бомбардировочный полк", 2], ["585-й женский авиаполк", 1], ["62-я армия", 3], ["64-я стрелковая дивизия", 2], ["8-я гвардейская армия", 1], ["88-й отдельный лыжный батальон", 1], ["Отдельная медико-санитарная рота", 1], ["Отдельный батальон связи №45", 1], ["Отдельный отряд собак-истребителей танков", 1], ["Отдельный отряд собак-миноискателей", 2]], "columns": ["unit_name", "total_soldiers"], "row_count": 29}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (70, 1, 13, 'Путь солдата', 'Подсчитайте количество солдат в каждой воинской части и выведите названия этих частей. Названия частей выведите в алфавитном порядке. Это покажет, какие подразделения были наиболее многочисленными', 'Объедините таблицы снаряжения, солдат и частей через `JOIN`', NULL, '{"data": [["1-й отдельный чехословацкий батальон", 2], ["1-й чехословацкий отдельный батальон", 1], ["1-я гвардейская танковая армия", 2], ["1-я морская бригада", 1], ["101-й инженерно-сапёрный батальон", 2], ["101-й полк НКВД", 1], ["101-й учебный полк", 1], ["106-я стрелковая дивизия", 1], ["14-я отдельная штрафная рота", 1], ["150-я стрелковая дивизия", 2], ["16-я воздушная армия", 2], ["18-я дивизия СС \"Хорст Вессель\"", 1], ["2-я ударная армия", 1], ["225-й отдельный инженерный батальон", 1], ["28-я дивизия народного ополчения", 1], ["3-я воздушная армия", 1], ["316-я стрелковая дивизия", 2], ["369-й отдельный батальон морской пехоты", 1], ["37-й гвардейский миномётный полк", 1], ["46-й гвардейский ночной бомбардировочный полк", 2], ["585-й женский авиаполк", 1], ["62-я армия", 3], ["64-я стрелковая дивизия", 2], ["8-я гвардейская армия", 1], ["88-й отдельный лыжный батальон", 1], ["Отдельная медико-санитарная рота", 1], ["Отдельный батальон связи №45", 1], ["Отдельный отряд собак-истребителей танков", 1], ["Отдельный отряд собак-миноискателей", 2]], "columns": ["unit_name", "total_soldiers"], "row_count": 29}', '{medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (48, 1, 20, 'Статистика ранений', 'Подсчитайте количество солдат по каждому статусу (status). Это основа для анализа людских потерь', 'Примените CTE для группировки по месяцам и `AVG` в оконной функции', NULL, '{"data": [["жив", 16], ["пропал без вести", 7], ["ранен", 8], ["убит", 9]], "columns": ["status", "count"], "row_count": 4}', '{cte,medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (23, 0, 23, 'Годовой отчет сражений', 'Определите, в какие годы начинались боевые операции, и подсчитайте их количество. Выведите год начала (как year) и количество (как battles_count). Отсортируйте по году. (Учитывайте только год начала start_date)', 'Извлеките год из даты с помощью `EXTRACT` и сгруппируйте по нему', NULL, '{"data": [[1941.0, 9], [1942.0, 6], [1943.0, 4], [1944.0, 4], [1945.0, 7]], "columns": ["year", "battles_count"], "row_count": 5}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (51, 1, 23, 'Цена победы', 'Определите, в какие годы начинались боевые операции, и подсчитайте их количество. Выведите год начала (как year) и количество (как battles_count). Отсортируйте по году. (Учитывайте только год начала start_date)', 'Примените CTE для раздельного подсчета потерь и `UNION` для объединения результатов', NULL, '{"data": [[1941.0, 9], [1942.0, 6], [1943.0, 4], [1944.0, 4], [1945.0, 7]], "columns": ["year", "battles_count"], "row_count": 5}', '{cte,stalingrad,medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (24, 0, 24, 'Возраст призывника', 'Рассчитайте возраст солдат на момент призыва (год призыва минус год рождения). Назовите колонку enlistment_age. Выведите ФИО и возраст.', 'Используйте функцию `AGE` для расчета разницы между датами', NULL, '{"data": [["Иванов Алексей Петрович", 18.0], ["Смирнова Анна Васильевна", 17.0], ["Петров Дмитрий Иванович", 23.0], ["Козлов Николай Семёнович", 21.0], ["Фёдорова Мария Ивановна", 21.0], ["Жуков Андрей Григорьевич", 26.0], ["Павлов Яков Фёдорович", 25.0], ["Зайцева Людмила Михайловна", 19.0], ["Громов Михаил Сергеевич", 23.0], ["Орлова Вера Павловна", 22.0], ["Новиков Александр Иванович", 20.0], ["Васнецова Татьяна Дмитриевна", 20.0], ["Кузнецов Пётр Васильевич", 25.0], ["Белов Алексей Николаевич", 19.0], ["Соколова Ольга Ивановна", 22.0], ["Морозов Иван Кузьмич", 27.0], ["Волкова Елена Сергеевна", 17.0], ["Ткаченко Григорий Петрович", 17.0], ["Беляев Павел Дмитриевич", 29.0], ["Семёнова Валентина Михайловна", 22.0], ["Ковалёв Сергей Николаевич", 18.0], ["Мельникова Галина Ивановна", 18.0], ["Фёдоров Игорь Васильевич", 28.0], ["Горбачёв Алексей Дмитриевич", 17.0], ["Сидорова Екатерина Петровна", 23.0], ["Смирнов Василий Иванович", 30.0], ["Крылова Надежда Фёдоровна", 18.0], ["Орлов Денис Сергеевич", 17.0], ["Жукова Елена Викторовна", 19.0], ["Гришин Алексей Петрович", 23.0], ["Ткаченко Иван Григорьевич", 21.0], ["Воронцова Лидия Павловна", 19.0], ["Жуковский Виктор Михайлович", 26.0], ["Морозова Анна Сергеевна", 20.0], ["Кузнецов Артём Игоревич", 17.0], ["Соколовская Надежда Викторовна", 18.0], ["Белов Дмитрий Николаевич", 25.0], ["Громова Екатерина Ивановна", 18.0], ["Фролов Павел Сергеевич", 16.0], ["Ковалёва Ольга Дмитриевна", 21.0]], "columns": ["full_name", "enlistment_age"], "row_count": 40}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (52, 1, 24, 'Рейтинг эффективности', 'Рассчитайте возраст солдат на момент призыва (год призыва минус год рождения). Назовите колонку enlistment_age. Выведите ФИО и возраст.', 'Примените `RANK()` и `DENSE_RANK()` для сортировки значений', NULL, '{"data": [["Иванов Алексей Петрович", 18.0], ["Смирнова Анна Васильевна", 17.0], ["Петров Дмитрий Иванович", 23.0], ["Козлов Николай Семёнович", 21.0], ["Фёдорова Мария Ивановна", 21.0], ["Жуков Андрей Григорьевич", 26.0], ["Павлов Яков Фёдорович", 25.0], ["Зайцева Людмила Михайловна", 19.0], ["Громов Михаил Сергеевич", 23.0], ["Орлова Вера Павловна", 22.0], ["Новиков Александр Иванович", 20.0], ["Васнецова Татьяна Дмитриевна", 20.0], ["Кузнецов Пётр Васильевич", 25.0], ["Белов Алексей Николаевич", 19.0], ["Соколова Ольга Ивановна", 22.0], ["Морозов Иван Кузьмич", 27.0], ["Волкова Елена Сергеевна", 17.0], ["Ткаченко Григорий Петрович", 17.0], ["Беляев Павел Дмитриевич", 29.0], ["Семёнова Валентина Михайловна", 22.0], ["Ковалёв Сергей Николаевич", 18.0], ["Мельникова Галина Ивановна", 18.0], ["Фёдоров Игорь Васильевич", 28.0], ["Горбачёв Алексей Дмитриевич", 17.0], ["Сидорова Екатерина Петровна", 23.0], ["Смирнов Василий Иванович", 30.0], ["Крылова Надежда Фёдоровна", 18.0], ["Орлов Денис Сергеевич", 17.0], ["Жукова Елена Викторовна", 19.0], ["Гришин Алексей Петрович", 23.0], ["Ткаченко Иван Григорьевич", 21.0], ["Воронцова Лидия Павловна", 19.0], ["Жуковский Виктор Михайлович", 26.0], ["Морозова Анна Сергеевна", 20.0], ["Кузнецов Артём Игоревич", 17.0], ["Соколовская Надежда Викторовна", 18.0], ["Белов Дмитрий Николаевич", 25.0], ["Громова Екатерина Ивановна", 18.0], ["Фролов Павел Сергеевич", 16.0], ["Ковалёва Ольга Дмитриевна", 21.0]], "columns": ["full_name", "enlistment_age"], "row_count": 40}', '{window,medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (25, 0, 25, 'Демография частей', 'Определите минимальный и максимальный возраст солдат на момент призыва в каждой части. Выведите название частей и минимальные (min) и максимальные (max) возраста. Отсортируйте по названию части по алфавиту.', 'Примените `MIN` и `MAX` к году рождения с группировкой по частям', NULL, '{"data": [["1-й отдельный чехословацкий батальон", 19.0, 25.0], ["1-й чехословацкий отдельный батальон", 18.0, 18.0], ["1-я гвардейская танковая армия", 21.0, 25.0], ["1-я морская бригада", 17.0, 17.0], ["101-й инженерно-сапёрный батальон", 16.0, 20.0], ["101-й полк НКВД", 22.0, 22.0], ["101-й учебный полк", 23.0, 23.0], ["106-я стрелковая дивизия", 20.0, 20.0], ["14-я отдельная штрафная рота", 27.0, 27.0], ["150-я стрелковая дивизия", 19.0, 19.0], ["16-я воздушная армия", 22.0, 26.0], ["18-я дивизия СС \"Хорст Вессель\"", 19.0, 19.0], ["2-я ударная армия", 23.0, 23.0], ["225-й отдельный инженерный батальон", 17.0, 17.0], ["28-я дивизия народного ополчения", 17.0, 17.0], ["3-я воздушная армия", 20.0, 20.0], ["316-я стрелковая дивизия", 18.0, 21.0], ["369-й отдельный батальон морской пехоты", 18.0, 18.0], ["37-й гвардейский миномётный полк", 30.0, 30.0], ["46-й гвардейский ночной бомбардировочный полк", 18.0, 26.0], ["585-й женский авиаполк", 28.0, 28.0], ["62-я армия", 17.0, 25.0], ["64-я стрелковая дивизия", 18.0, 21.0], ["8-я гвардейская армия", 22.0, 22.0], ["88-й отдельный лыжный батальон", 29.0, 29.0], ["Отдельная медико-санитарная рота", 17.0, 17.0], ["Отдельный батальон связи №45", 18.0, 18.0], ["Отдельный отряд собак-истребителей танков", 23.0, 23.0], ["Отдельный отряд собак-миноискателей", 17.0, 21.0]], "columns": ["unit_name", "min", "max"], "row_count": 29}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (74, 1, 25, 'Хронология призыва', 'Определите минимальный и максимальный возраст солдат на момент призыва в каждой части. Выведите название частей и минимальные (min) и максимальные (max) возраста. Отсортируйте по названию части по алфавиту.', 'Используйте `ROW_NUMBER()` с группировкой по частям и сортировкой по дате', NULL, '{"data": [["1-й отдельный чехословацкий батальон", 19.0, 25.0], ["1-й чехословацкий отдельный батальон", 18.0, 18.0], ["1-я гвардейская танковая армия", 21.0, 25.0], ["1-я морская бригада", 17.0, 17.0], ["101-й инженерно-сапёрный батальон", 16.0, 20.0], ["101-й полк НКВД", 22.0, 22.0], ["101-й учебный полк", 23.0, 23.0], ["106-я стрелковая дивизия", 20.0, 20.0], ["14-я отдельная штрафная рота", 27.0, 27.0], ["150-я стрелковая дивизия", 19.0, 19.0], ["16-я воздушная армия", 22.0, 26.0], ["18-я дивизия СС \"Хорст Вессель\"", 19.0, 19.0], ["2-я ударная армия", 23.0, 23.0], ["225-й отдельный инженерный батальон", 17.0, 17.0], ["28-я дивизия народного ополчения", 17.0, 17.0], ["3-я воздушная армия", 20.0, 20.0], ["316-я стрелковая дивизия", 18.0, 21.0], ["369-й отдельный батальон морской пехоты", 18.0, 18.0], ["37-й гвардейский миномётный полк", 30.0, 30.0], ["46-й гвардейский ночной бомбардировочный полк", 18.0, 26.0], ["585-й женский авиаполк", 28.0, 28.0], ["62-я армия", 17.0, 25.0], ["64-я стрелковая дивизия", 18.0, 21.0], ["8-я гвардейская армия", 22.0, 22.0], ["88-й отдельный лыжный батальон", 29.0, 29.0], ["Отдельная медико-санитарная рота", 17.0, 17.0], ["Отдельный батальон связи №45", 18.0, 18.0], ["Отдельный отряд собак-истребителей танков", 23.0, 23.0], ["Отдельный отряд собак-миноискателей", 17.0, 21.0]], "columns": ["unit_name", "min", "max"], "row_count": 29}', '{medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (26, 0, 26, 'Городская аналитика', 'Вычислите средний возраст солдат на момент призыва по городам призыва. Выведите название города и средний возраст как avg_age. Результат округлите до целого, а города выведите в обратном алфавитном порядке.', 'Группировка по городам с использованием `AVG` и арифметических операций. Округление с помощью `ROUND`', NULL, '{"data": [["Челябинск", 18.0], ["Харьков", 22.0], ["Тула", 27.0], ["Сталинград", 19.0], ["Смоленск", 20.0], ["Севастополь", 18.0], ["Свердловск", 23.0], ["Самара", 29.0], ["Ростов-на-Дону", 20.0], ["Омск", 22.0], ["Одесса", 20.0], ["Новосибирск", 25.0], ["Мурманск", 25.0], ["Москва", 18.0], ["Минск", 25.0], ["Ленинград", 18.0], ["Киев", 23.0], ["Казань", 28.0], ["Горький", 18.0], ["Воронеж", 17.0], ["Волгоград", 25.0], ["Брянск", 17.0]], "columns": ["enlistment_city", "avg_age"], "row_count": 22}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (53, 1, 26, 'Циклы пополнения', 'Вычислите средний возраст солдат на момент призыва по городам призыва. Выведите название города и средний возраст как avg_age. Результат округлите до целого, а города выведите в обратном алфавитном порядке.', 'Используйте `LAG()` и `LEAD()` для навигации по датам в рамках части', NULL, '{"data": [["Челябинск", 18.0], ["Харьков", 22.0], ["Тула", 27.0], ["Сталинград", 19.0], ["Смоленск", 20.0], ["Севастополь", 18.0], ["Свердловск", 23.0], ["Самара", 29.0], ["Ростов-на-Дону", 20.0], ["Омск", 22.0], ["Одесса", 20.0], ["Новосибирск", 25.0], ["Мурманск", 25.0], ["Москва", 18.0], ["Минск", 25.0], ["Ленинград", 18.0], ["Киев", 23.0], ["Казань", 28.0], ["Горький", 18.0], ["Воронеж", 17.0], ["Волгоград", 25.0], ["Брянск", 17.0]], "columns": ["enlistment_city", "avg_age"], "row_count": 22}', '{window,medium}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (28, 0, 28, 'История воинских частей', 'Сгруппируйте части по году формирования и подсчитайте их количество. Выведите год формирования (как formation_year) и количество частей (как units_count). Отсортируйте по году формирования.', 'Извлеките год из `formation_date` с помощью `EXTRACT`', NULL, '{"data": [[1939.0, 1], [1941.0, 8], [1942.0, 12], [1943.0, 8], [1944.0, 1]], "columns": ["formation_year", "units_count"], "row_count": 5}', '{easy}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (106, 5, 1, 'Возраст призыва', 'Напишите скалярную функцию get_enlistment_age(p_soldier_id INT), возвращающую возраст солдата на момент призыва (год призыва из enlistment_date минус birth_year).', 'Используйте CREATE OR REPLACE FUNCTION get_enlistment_age(p_soldier_id INT) RETURNS INT AS $$ ... $$ LANGUAGE plpgsql;', 'CREATE OR REPLACE FUNCTION get_enlistment_age(p_soldier_id INT) RETURNS INT AS $$ DECLARE v_age INT; BEGIN SELECT (EXTRACT(YEAR FROM enlistment_date) - birth_year)::INT INTO v_age FROM soldier WHERE id = p_soldier_id; RETURN v_age; END; $$ LANGUAGE plpgsql;', '{"mode": "ddl", "test_query": "SELECT get_enlistment_age(1);", "columns": ["get_enlistment_age"], "data": [[18]]}', '{plpgsql,function,scalar,mission5}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (107, 5, 2, 'Бойцы подразделения', 'Напишите табличную функцию get_unit_soldiers(p_unit_name VARCHAR), возвращающую таблицу (full_name VARCHAR, enlistment_city VARCHAR) с бойцами, служившими в указанной части.', 'Используйте RETURNS TABLE (full_name VARCHAR, enlistment_city VARCHAR) и RETURN QUERY SELECT s.full_name, s.enlistment_city FROM soldier s JOIN military_service ms ON s.id = ms.soldier_id JOIN military_unit mu ON ms.unit_id = mu.id WHERE mu.unit_name = p_unit_name;', 'CREATE OR REPLACE FUNCTION get_unit_soldiers(p_unit_name VARCHAR) RETURNS TABLE (full_name VARCHAR, enlistment_city VARCHAR) AS $$ BEGIN RETURN QUERY SELECT s.full_name, s.enlistment_city FROM soldier s JOIN military_service ms ON s.id = ms.soldier_id JOIN military_unit mu ON ms.unit_id = mu.id WHERE mu.unit_name = p_unit_name; END; $$ LANGUAGE plpgsql;', '{"mode": "ddl", "test_query": "SELECT * FROM get_unit_soldiers(''1-я морская бригада'') ORDER BY full_name;", "columns": ["full_name", "enlistment_city"], "data": [["Волкова Елена Сергеевна", "Ленинград"]]}', '{plpgsql,function,table_function,mission5}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (108, 5, 3, 'Перевод военнослужащего', 'Напишите хранимую процедуру transfer_soldier(p_soldier_id INT, p_new_unit_id INT), которая переводит солдата в новую часть: закрывает текущую службу (end_date = CURRENT_DATE, где end_date IS NULL) и создает новую запись о службе с unit_id = p_new_unit_id и start_date = CURRENT_DATE.', 'Используйте CREATE OR REPLACE PROCEDURE transfer_soldier(p_soldier_id INT, p_new_unit_id INT) AS $$ BEGIN UPDATE military_service SET end_date = CURRENT_DATE WHERE soldier_id = p_soldier_id AND end_date IS NULL; INSERT INTO military_service (soldier_id, unit_id, start_date) VALUES (p_soldier_id, p_new_unit_id, CURRENT_DATE); END; $$ LANGUAGE plpgsql;', 'CREATE OR REPLACE PROCEDURE transfer_soldier(p_soldier_id INT, p_new_unit_id INT) AS $$ BEGIN UPDATE military_service SET end_date = CURRENT_DATE WHERE soldier_id = p_soldier_id AND end_date IS NULL; INSERT INTO military_service (soldier_id, unit_id, start_date) VALUES (p_soldier_id, p_new_unit_id, CURRENT_DATE); END; $$ LANGUAGE plpgsql;', '{"mode": "ddl", "test_query": "CALL transfer_soldier(1, 2); SELECT unit_id FROM military_service WHERE soldier_id = 1 ORDER BY id DESC LIMIT 1;", "columns": ["unit_id"], "data": [[2]]}', '{plpgsql,procedure,mission5}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (109, 5, 4, 'Аудит поступления техники', 'Создайте триггерную функцию log_equipment_addition() и триггер trg_after_equipment_insert на таблице equipment (AFTER INSERT FOR EACH ROW), который при добавлении новой техники записывает в таблицу equipment_audit строку с item_name (NEW.item_name) и added_at (CURRENT_DATE).', 'Триггерная функция должна иметь RETURNS TRIGGER, выполнять INSERT INTO equipment_audit (item_name, added_at) VALUES (NEW.item_name, CURRENT_DATE); RETURN NEW; а триггер: CREATE TRIGGER trg_after_equipment_insert AFTER INSERT ON equipment FOR EACH ROW EXECUTE FUNCTION log_equipment_addition();', 'CREATE OR REPLACE FUNCTION log_equipment_addition() RETURNS TRIGGER AS $$ BEGIN INSERT INTO equipment_audit (item_name, added_at) VALUES (NEW.item_name, CURRENT_DATE); RETURN NEW; END; $$ LANGUAGE plpgsql; CREATE TRIGGER trg_after_equipment_insert AFTER INSERT ON equipment FOR EACH ROW EXECUTE FUNCTION log_equipment_addition();', '{"mode": "ddl", "test_query": "INSERT INTO equipment (id, unit_id, equipment_type, item_name, quantity, last_replenishment) VALUES (9999, 1, ''тест'', ''Тестовый образец'', 1, CURRENT_DATE); SELECT item_name FROM equipment_audit WHERE item_name = ''Тестовый образец'';", "columns": ["item_name"], "data": [["Тестовый образец"]]}', '{plpgsql,trigger,audit,mission5}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;

INSERT INTO public.tasks (task_global_id, mission_id, task_id, title, description, clue, correct_query, expected_result, tags) VALUES (110, 5, 5, 'Контроль возраста призыва', 'Создайте триггерную функцию validate_soldier_age() и триггер trg_before_soldier_insert на таблице soldier (BEFORE INSERT FOR EACH ROW), который проверяет возраст бойца: если EXTRACT(YEAR FROM NEW.enlistment_date) - NEW.birth_year < 16, вызывается ошибка RAISE EXCEPTION ''Возраст призывника не может быть меньше 16 лет''. В остальных случаях возвращается NEW.', 'В теле триггерной функции проверьте IF (EXTRACT(YEAR FROM NEW.enlistment_date) - NEW.birth_year) < 16 THEN RAISE EXCEPTION ''Возраст призывника не может быть меньше 16 лет''; END IF; RETURN NEW;', 'CREATE OR REPLACE FUNCTION validate_soldier_age() RETURNS TRIGGER AS $$ BEGIN IF (EXTRACT(YEAR FROM NEW.enlistment_date) - NEW.birth_year) < 16 THEN RAISE EXCEPTION ''Возраст призывника не может быть меньше 16 лет''; END IF; RETURN NEW; END; $$ LANGUAGE plpgsql; CREATE TRIGGER trg_before_soldier_insert BEFORE INSERT ON soldier FOR EACH ROW EXECUTE FUNCTION validate_soldier_age();', '{"mode": "ddl", "test_query": "INSERT INTO soldier (id, full_name, birth_year, rank, branch, enlistment_city, enlistment_date) VALUES (9999, ''Малолетний боец'', 1930, ''рядовой'', ''пехота'', ''Москва'', ''1941-01-01'');", "expect_error": true}', '{plpgsql,trigger,validation,mission5}')
ON CONFLICT (task_global_id) DO UPDATE SET
    mission_id = EXCLUDED.mission_id,
    task_id = EXCLUDED.task_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    clue = EXCLUDED.clue,
    correct_query = EXCLUDED.correct_query,
    expected_result = EXCLUDED.expected_result,
    tags = EXCLUDED.tags;
SELECT pg_catalog.setval('public.tasks_task_global_id_seq', 110, true);
