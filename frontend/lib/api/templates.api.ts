/**
 * Templates API
 * Template management endpoints
 */
import { apiClient } from "./client";
import { Template, TemplateConfig } from "../types/template.types";
import { AxiosRequestHeaders } from "axios";

export const templatesAPI = {
  /**
   * Create new template by analyzing PDF
   */
  async create(file: File, templateName: string) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("template_name", templateName);

    const response = await apiClient.post("/v1/templates", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      } as unknown as AxiosRequestHeaders,
    });

    return response.data.data!;
  },

  /**
   * List all templates
   */
  async list(
    search?: string,
    page?: number,
    limit?: number,
    template_id?: number | null,
    
  ): Promise<{ templates: Template[]; count: number }> {
    let listUrl = "/v1/templates";
    if (search) {
      listUrl += "?search=" + search;
    }
    if (page) {
      listUrl += "?page=" + page;
    }
    if (limit) {
      listUrl += "?limit=" + limit;
    }
    if (template_id) {
      listUrl += "?template_id=" + template_id;
    }
    const response = await apiClient.get<{ templates: Template[] }>(listUrl);
    return {
      templates: response.data.data!.templates,
      count: (response.data.meta?.count as number) || 0,
    };
  },

  /**
   * Get template by ID
   */
  async getById(templateId: number, includeConfig: boolean = true) {
    const url = `/v1/templates/${templateId}${
      includeConfig ? "?include_config=true" : ""
    }`;
    const response = await apiClient.get<{
      template: Template & { config?: TemplateConfig };
    }>(url);
    return response.data.data!;
  },

  /**
   * Delete template
   */
  async delete(templateId: number) {
    const response = await apiClient.delete<{ template_id: number }>(
      `/v1/templates/${templateId}`
    );
    return response.data.data!;
  },

  async getPreviewConfig(templateId: number) {
    const response = await apiClient.get<{ config: TemplateConfig }>(
      `/v1/preview/config/${templateId}`
    );
    return response.data.data!;
  },
};
