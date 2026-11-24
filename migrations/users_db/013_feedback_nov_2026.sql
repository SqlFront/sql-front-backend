--
-- Migration: 013_feedback_nov_2026.sql
-- Feature: curriculum-and-tasks
-- Description: Clarify descriptions and clues for Tasks 0.25, 1.3, 2.2, 1.17 based on November 2026 student feedback
--

-- Task 0.25 (task_global_id = 25, «Демография частей»)
UPDATE public.tasks
SET description = 'Определите минимальный и максимальный возраст солдат на момент зачисления в каждую часть (используйте дату начала службы ms.start_date и год рождения s.birth_year). Выведите название частей и минимальные (min) и максимальные (max) возраста. Отсортируйте по названию части по алфавиту.

Поля в результирующей таблице: `unit_name`, `min`, `max`',
    clue = 'Используйте ms.start_date для расчета возраста на момент начала службы в части: MIN(EXTRACT(YEAR FROM ms.start_date) - s.birth_year).'
WHERE task_global_id = 25;

-- Task 1.3 (task_global_id = 38, «Поиск героев для награждения»)
UPDATE public.tasks
SET description = 'Выявите 20 солдат, участвовавших в наибольшем количестве сражений, и присвойте им ранги. Вычисленные столбцы назовите battles_participated и hero_rank. Это основа для награждения орденами и медалями. Учитывайте только те сражения, даты проведения которых пересекаются с периодом службы бойца в части (ms.start_date <= b.end_date и (ms.end_date IS NULL или ms.end_date >= b.start_date)). Присвойте ранг с помощью функции DENSE_RANK() по убыванию числа сражений, а при равенстве — по алфавиту full_name.

Поля в результирующей таблице: `full_name`, `battles_participated`, `hero_rank`',
    clue = 'Соедините soldier, military_service, battle_military_unit и battle. Условие пересечения дат: ms.start_date <= b.end_date AND (ms.end_date IS NULL OR ms.end_date >= b.start_date). Функция ранжирования: DENSE_RANK() OVER (ORDER BY COUNT(DISTINCT b.id) DESC, s.full_name).'
WHERE task_global_id = 38;

-- Task 2.2 (task_global_id = 78, «Сравнение стратегий»)
UPDATE public.tasks
SET description = 'Сравните среднюю боевую эффективность частей, участвовавших в стратегических и локальных операциях. К стратегическим операциям относятся битвы с уровнем важности «стратегическая», к локальным — все остальные («фронтовая», «тактическая»).

Формат результата (столбцы строго в указанном порядке):
1. battle_group — группа операций: строка ''Стратегические битвы'' (для уровня важности «стратегическая») или ''Локальные операции'' (для остальных уровней);
2. avg_efficiency — средняя боевая эффективность задействованных подразделений (округленная до 2 знаков).

Поля в результирующей таблице: `battle_group`, `avg_efficiency`
Примечание: округленная до 2 знаков.'
WHERE task_global_id = 78;

-- Task 1.17 (task_global_id = 44, «Участники Сталинграда»)
UPDATE public.tasks
SET description = 'Найдите всех солдат, служивших в частях, дислоцированных в Сталинграде (location = ''Сталинград''). Это основа для создания мемориальных списков.

Поля в результирующей таблице: `full_name`
Примечание: Отсортируйте результат по алфавиту full_name; учитывайте только место дислокации подразделения в military_unit (location = ''Сталинград''). Соединение с таблицей сражений battle не требуется.'
WHERE task_global_id = 44;
