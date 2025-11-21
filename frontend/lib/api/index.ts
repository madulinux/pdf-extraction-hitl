/**
 * API Index
 * Export all API modules
 */
export { apiClient } from './client';
export { authAPI } from './auth.api';
export { templatesAPI } from './templates.api';
export { extractionAPI } from './extraction.api';
export { learningAPI } from './learning.api';

// Re-export types
export type * from '../types/auth.types';
export type * from '../types/template.types';
export type * from '../types/extraction.types';
export type * from '../types/learning.types';
export type * from '../types/common.types';
