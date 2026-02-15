/**
 * Extraction API
 * Document extraction endpoints
 */
import { apiClient } from "./client";
import {
  Document,
  ExtractionResult,
  ExtractResponse,
  ValidationResponse,
} from "../types/extraction.types";
import { AxiosRequestHeaders } from "axios";

export const extractionAPI = {
  /**
   * Extract data from document
   */
  async extract(file: File, templateId: number): Promise<ExtractResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("template_id", templateId.toString());

    const response = await apiClient.post("/v1/extraction/extract", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      } as unknown as AxiosRequestHeaders,
    });

    return response.data.data as ExtractResponse;
  },

  /**
   * Submit corrections/validation
   */
  async submitValidation(
    documentId: number,
    corrections: Record<string, string>
  ): Promise<ValidationResponse> {
    const response = await apiClient.post("/v1/extraction/validate", {
      document_id: documentId,
      corrections,
    });

    return response.data.data as ValidationResponse;
  },

  /**
   * List all documents
   */
  async listDocuments({
    search = "",
    page = 1,
    pageSize = 10,
    templateId = undefined,
    status = "all",
  }: {
    search?: string;
    page?: number;
    pageSize?: number;
    templateId?: number | undefined;
    status?: "all" | "validated" | "extracted" | "pending";
  }): Promise<{ documents: Document[]; meta: Record<string, string> }> {
    const params = new URLSearchParams({
      page: page?.toString() || "1",
      page_size: pageSize?.toString() || "10",
      search: search || "",
    });

    if (typeof templateId === "number") {
      params.set("template_id", templateId.toString());
    }

    if (status && status !== "all") {
      params.set("status", status);
    }
    const apiUrl = `/v1/extraction/documents?${params.toString()}`;

    const response = await apiClient.get<{ documents: Document[] }>(apiUrl);
    return {
      documents: response.data.data!.documents,
      meta: response.data.meta as Record<string, string>,
    };
  },

  /**
   * Get document by ID
   */
  async getById(
    documentId: number
  ): Promise<{ document: Document & { results: ExtractionResult } }> {
    const response = await apiClient.get<{
      document: Document & { results: ExtractionResult };
    }>(`/v1/extraction/documents/${documentId}`);
    return response.data.data!;
  },

  /**
   * Extract data from multiple documents in bulk
   */
  async extractBulk(
    files: File[],
    templateId: number
  ): Promise<{
    total: number;
    successful: number;
    failed: number;
    documents: Array<{
      document_id: number;
      filename: string;
      status: string;
      results: ExtractionResult;
    }>;
    errors: Array<{
      filename: string;
      error: string;
    }>;
  }> {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append("files", file);
    });
    formData.append("template_id", templateId.toString());

    const response = await apiClient.post(
      "/v1/extraction/extract/bulk",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        } as unknown as AxiosRequestHeaders,
      }
    );

    return response.data.data as {
      total: number;
      successful: number;
      failed: number;
      documents: Array<{
        document_id: number;
        filename: string;
        status: string;
        results: ExtractionResult;
      }>;
      errors: Array<{
        filename: string;
        error: string;
      }>;
    };
  },

  /**
   * Export extraction results to Excel
   */
  async exportToExcel(
    templateId: number,
    options: {
      status?: 'all' | 'validated' | 'pending';
      includeMetadata?: boolean;
    } = {}
  ): Promise<Blob> {
    const { status = 'all', includeMetadata = true } = options;
    
    const params = new URLSearchParams({
      status,
      include_metadata: includeMetadata.toString(),
    });

    const response = await apiClient.getBlob(
      `/v1/extraction/export/${templateId}?${params.toString()}`
    );

    return response.data;
  },
};
