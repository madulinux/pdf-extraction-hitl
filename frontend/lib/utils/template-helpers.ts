/**
 * Template Helper Functions
 * Utilities for handling template configurations
 */

import { FieldInfo, FieldLocation } from '@/lib/types/template.types';

/**
 * Get all locations for a field (backward compatible)
 * Supports both old format (single location) and new format (locations array)
 */
export function getFieldLocations(field: FieldInfo): FieldLocation[] {
  // New format: locations array
  if (field.locations && Array.isArray(field.locations)) {
    return field.locations;
  }
  
  // Old format: single location
  if (field.location) {
    return [{
      page: field.location.page,
      x0: field.location.x0,
      y0: field.location.y0,
      x1: field.location.x1,
      y1: field.location.y1,
      context: field.context || {
        label: null,
        label_position: null,
        words_before: [],
        words_after: []
      }
    }];
  }
  
  return [];
}

/**
 * Get location count for a field
 */
export function getLocationCount(field: FieldInfo): number {
  return getFieldLocations(field).length;
}

/**
 * Check if field has multiple locations
 */
export function hasMultipleLocations(field: FieldInfo): boolean {
  return getLocationCount(field) > 1;
}

/**
 * Get pages where field appears
 */
export function getFieldPages(field: FieldInfo): number[] {
  const locations = getFieldLocations(field);
  return [...new Set(locations.map(loc => loc.page))].sort();
}

/**
 * Get field summary for display
 */
export function getFieldSummary(fieldName: string, field: FieldInfo): string {
  const locations = getFieldLocations(field);
  const pageCount = getFieldPages(field).length;
  const locationCount = locations.length;
  
  if (locationCount === 0) {
    return `${fieldName} (no location)`;
  }
  
  if (locationCount === 1) {
    const loc = locations[0];
    const label = loc.context.label ? ` - ${loc.context.label}` : '';
    return `${fieldName} (Page ${loc.page + 1}${label})`;
  }
  
  return `${fieldName} (${locationCount} locations, ${pageCount} pages)`;
}

/**
 * Format context information for display
 */
export function formatContextInfo(field: FieldInfo): string {
  const locations = getFieldLocations(field);
  
  if (locations.length === 0) {
    return 'No context';
  }
  
  const contextParts: string[] = [];
  
  locations.forEach((loc, idx) => {
    const parts: string[] = [];
    
    if (loc.context.label) {
      parts.push(`Label: "${loc.context.label}"`);
    }
    
    if (loc.context.words_before.length > 0) {
      parts.push(`${loc.context.words_before.length} words before`);
    }
    
    if (loc.context.words_after.length > 0) {
      parts.push(`${loc.context.words_after.length} words after`);
    }
    
    if (parts.length > 0) {
      const prefix = locations.length > 1 ? `Location ${idx + 1}: ` : '';
      contextParts.push(prefix + parts.join(', '));
    }
  });
  
  return contextParts.length > 0 ? contextParts.join(' | ') : 'No context';
}
