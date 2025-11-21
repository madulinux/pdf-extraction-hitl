/**
 * Common Types
 * Shared types across the application
 */

export interface APIResponse<T = unknown> {
  success: boolean;
  message: string;
  data: T | null;
  timestamp: string;
  meta?: Record<string, unknown>;
  errors?: Record<string, string>;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export interface LoadingState {
  isLoading: boolean;
  error: string | null;
}
