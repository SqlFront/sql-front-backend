--
-- Migration: 006_mission_3_clue_syntax.sql
-- Feature: mission-3-multiline-ddl-syntax
-- Description: Clarify clue for task 3.2 requiring semicolon separation and remove Semen lore reference
--

UPDATE public.tasks
SET description = 'Центр принимает донесения по единому времени, а набирать «podpolye.» перед каждым именем таблицы в полутьме — верный способ ошибиться. Командование штаба требует настроить базу один раз и навсегда.

Настройте базу quest_sandbox: часовой пояс по умолчанию — ''UTC'', а путь поиска схем — сначала podpolye, затем public.',
    clue = 'Параметры уровня базы задаются оператором ALTER DATABASE <имя> SET <параметр> TO <значение>. Обязательно разделяйте операторы точкой с запятой (;).'
WHERE (mission_id = 3 AND task_id = 2) OR task_global_id = 85;
