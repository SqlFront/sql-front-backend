--
-- Migration: 011_add_user_query_to_tasks_solved.sql
-- Feature: curriculum-and-tasks / sql-engine
-- Description: Add user_query and updated_at to tasks_solved for solution persistence
--

ALTER TABLE public.tasks_solved
ADD COLUMN IF NOT EXISTS user_query text,
ADD COLUMN IF NOT EXISTS updated_at timestamp without time zone DEFAULT now();
