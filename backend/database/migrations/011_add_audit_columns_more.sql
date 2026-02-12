-- 011_add_audit_columns_more.sql
-- Add audit columns (created_by, updated_by) to remaining tables

ALTER TABLE users ADD COLUMN created_by INTEGER;
ALTER TABLE users ADD COLUMN updated_by INTEGER;

ALTER TABLE template_configs ADD COLUMN updated_by INTEGER;

ALTER TABLE field_configs ADD COLUMN created_by INTEGER;
ALTER TABLE field_configs ADD COLUMN updated_by INTEGER;

ALTER TABLE field_locations ADD COLUMN created_by INTEGER;
ALTER TABLE field_locations ADD COLUMN updated_by INTEGER;

ALTER TABLE field_contexts ADD COLUMN created_by INTEGER;
ALTER TABLE field_contexts ADD COLUMN updated_by INTEGER;

ALTER TABLE learned_patterns ADD COLUMN created_by INTEGER;
ALTER TABLE learned_patterns ADD COLUMN updated_by INTEGER;

ALTER TABLE pattern_learning_jobs ADD COLUMN created_by INTEGER;
ALTER TABLE pattern_learning_jobs ADD COLUMN updated_by INTEGER;

ALTER TABLE pattern_statistics ADD COLUMN created_by INTEGER;
ALTER TABLE pattern_statistics ADD COLUMN updated_by INTEGER;

ALTER TABLE jobs ADD COLUMN created_by INTEGER;
ALTER TABLE jobs ADD COLUMN updated_by INTEGER;

ALTER TABLE failed_jobs ADD COLUMN created_by INTEGER;
ALTER TABLE failed_jobs ADD COLUMN updated_by INTEGER;

ALTER TABLE training_history ADD COLUMN created_by INTEGER;
ALTER TABLE training_history ADD COLUMN updated_by INTEGER;

ALTER TABLE data_quality_metrics ADD COLUMN created_by INTEGER;
ALTER TABLE data_quality_metrics ADD COLUMN updated_by INTEGER;

ALTER TABLE strategy_performance ADD COLUMN created_by INTEGER;
ALTER TABLE strategy_performance ADD COLUMN updated_by INTEGER;
