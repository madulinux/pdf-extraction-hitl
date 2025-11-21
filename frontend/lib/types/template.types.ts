/**
 * Template Types
 */

export interface Template {
  id: number;
  name: string;
  filename: string;
  config_path: string;
  field_count: number;
  created_at: string;
  updated_at: string;
  status: string;
}

export interface TemplateSelectOption extends Template {
  label?: string;
}

export interface TemplateConfig {
  template_name?: string;
  total_pages?: number;
  fields: Record<string, FieldInfo>;
  metadata: {
    field_count: number;
    pages: number;
    analyzed_at?: string | null;
  };
}

export interface ContextWord {
  text: string;
  x: number;
  y: number;
}

export interface FieldContext {
  label: string | null;
  label_position: {
    x0: number;
    y0: number;
    x1: number;
    y1: number;
  } | null;
  words_before: ContextWord[];
  words_after: ContextWord[];
}

export interface FieldLocation {
  page: number;
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  context: FieldContext;
}

export interface FieldInfo {
  marker_text?: string;
  // Support both old and new formats
  location?: {
    page: number;
    x0: number;
    y0: number;
    x1: number;
    y1: number;
  };
  locations?: FieldLocation[];
  context?: FieldContext;
  pattern?: string | null;
  regex_pattern?: string;
  extraction_strategy?: string;
}

export interface PreviewConfigResponse {
  template_id: number;
  template_name: string;
  filename: string;
  config: TemplateConfig;
}
