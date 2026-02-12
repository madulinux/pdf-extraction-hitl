-- 010_add_audit_columns.sql
-- Add audit columns (created_by, updated_by) for blamable tracking

ALTER TABLE templates ADD COLUMN created_by INTEGER;
ALTER TABLE templates ADD COLUMN updated_by INTEGER;

ALTER TABLE documents ADD COLUMN created_by INTEGER;
ALTER TABLE documents ADD COLUMN updated_by INTEGER;

ALTER TABLE feedback ADD COLUMN created_by INTEGER;
ALTER TABLE feedback ADD COLUMN updated_by INTEGER;
