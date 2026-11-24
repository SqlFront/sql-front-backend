-- Migration 003 for game_db: Add sequence for military_service.id (Task 5.3)
CREATE SEQUENCE IF NOT EXISTS public.military_service_id_seq;
ALTER TABLE public.military_service ALTER COLUMN id SET DEFAULT nextval('public.military_service_id_seq');
SELECT setval('public.military_service_id_seq', COALESCE((SELECT MAX(id) FROM public.military_service), 0) + 1, false);
ALTER SEQUENCE public.military_service_id_seq OWNED BY public.military_service.id;
GRANT USAGE, SELECT, UPDATE ON SEQUENCE public.military_service_id_seq TO sql_runner;
