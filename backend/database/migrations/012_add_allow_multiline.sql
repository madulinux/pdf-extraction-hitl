-- 012_add_allow_multiline.sql
-- Add allow_multiline flag to field_configs

ALTER TABLE field_configs ADD COLUMN allow_multiline INTEGER;
