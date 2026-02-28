-- Migration 003: add last_reply column to profiles for follow-up detection
-- Apply via Supabase SQL Editor.

ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS last_reply TEXT;
