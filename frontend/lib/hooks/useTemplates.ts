/**
 * useTemplates Hook
 * Templates management
 */
'use client';

import { useState, useCallback } from 'react';
import { templatesAPI } from '../api/templates.api';
import { Template } from '../types/template.types';

export function useTemplates() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTemplates = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const { templates: data } = await templatesAPI.list();
      setTemplates(data);
      
      return { success: true, data };
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch templates';
      setError(message);
      return { success: false, error: message };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createTemplate = useCallback(async (file: File, name: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const result = await templatesAPI.create(file, name);
      
      // Refresh list
      await fetchTemplates();
      
      return { success: true, data: result };
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create template';
      setError(message);
      return { success: false, error: message };
    } finally {
      setIsLoading(false);
    }
  }, [fetchTemplates]);

  const deleteTemplate = useCallback(async (templateId: number) => {
    try {
      setIsLoading(true);
      setError(null);
      
      await templatesAPI.delete(templateId);
      
      // Refresh list
      await fetchTemplates();
      
      return { success: true };
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete template';
      setError(message);
      return { success: false, error: message };
    } finally {
      setIsLoading(false);
    }
  }, [fetchTemplates]);

  return {
    templates,
    isLoading,
    error,
    fetchTemplates,
    createTemplate,
    deleteTemplate,
  };
}
