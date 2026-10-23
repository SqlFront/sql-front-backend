-- Make task_id nullable in user_events since auth events (password reset, login, logout) do not belong to a specific task.
ALTER TABLE public.user_events ALTER COLUMN task_id DROP NOT NULL;
