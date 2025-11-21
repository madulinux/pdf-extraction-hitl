"use client";

import { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  AlertCircle,
  RefreshCw,
  Edit2,
  Save,
  X,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { templatesAPI } from "@/lib/api/templates.api";
import { TemplateConfig, FieldInfo } from "@/lib/types/template.types";
import { getFieldLocations, getLocationCount } from "@/lib/utils/template-helpers";
import Image from "next/image";
import { ScrollArea } from "./ui/scroll-area";

interface TemplatePreviewProps {
  templateId: number;
}

export default function TemplatePreview({ templateId }: TemplatePreviewProps) {
  const [config, setConfig] = useState<TemplateConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [selectedField, setSelectedField] = useState<string | null>(null);
  const [imageKey, setImageKey] = useState(0);
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<{
    context_label: string;
    regex_pattern: string;
  }>({
    context_label: "",
    regex_pattern: "",
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loadingPages, setLoadingPages] = useState(false);

  const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    loadTemplateData();
    loadPageCount();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [templateId]);

  const loadTemplateData = async () => {
    try {
      setLoading(true);
      setError("");

      // Load config using API client
      const data = await templatesAPI.getPreviewConfig(templateId);
      setConfig(data.config);
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : "Gagal memuat konfigurasi template";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const loadPageCount = async () => {
    try {
      setLoadingPages(true);
      const token = localStorage.getItem("access_token");
      const response = await fetch(
        `${API_BASE_URL}/v1/preview/pages/${templateId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      const result = await response.json();
      if (result.success) {
        setTotalPages(result.data.total_pages);
      }
    } catch (err) {
      console.error("Failed to load page count:", err);
      // Default to 1 page if fails
      setTotalPages(1);
    } finally {
      setLoadingPages(false);
    }
  };

  const handleFieldClick = (fieldName: string) => {
    const newSelectedField = selectedField === fieldName ? null : fieldName;
    setSelectedField(newSelectedField);
    // Force image reload with new highlight
    setImageKey((prev) => prev + 1);
  };

  // Group fields by page
  const getFieldsByPage = () => {
    if (!config) return {};

    const fieldsByPage: Record<number, Array<[string, FieldInfo]>> = {};

    Object.entries(config.fields).forEach(([fieldName, field]) => {
      
      if (!field.locations) {
        return;
      }

      const page = (field.locations?.[0]?.page ?? 0) + 1; // Convert to 1-indexed
      if (!fieldsByPage[page]) {
        fieldsByPage[page] = [];
      }
      fieldsByPage[page].push([fieldName, field]);
    });

    return fieldsByPage;
  };

  // Handle tab change - sync with preview page
  const handlePageTabChange = (pageStr: string) => {
    const page = parseInt(pageStr);
    setCurrentPage(page);
    setImageKey((prev) => prev + 1);
  };

  const getImageUrl = (page: number = currentPage) => {
    const token = localStorage.getItem("access_token");
    const baseUrl = `${API_BASE_URL}/v1/preview/template/${templateId}`;
    const params = new URLSearchParams({
      page: page.toString(),
      token: token || "",
      key: imageKey.toString(),
    });
    if (selectedField) {
      params.append("highlight_field", selectedField);
    }
    return `${baseUrl}?${params.toString()}`;
  };

  const handleEditField = (fieldName: string, field: FieldInfo) => {
    setEditingField(fieldName);
    const locations = getFieldLocations(field);
    const firstLocation = locations[0];
    setEditValues({
      context_label: firstLocation?.context?.label || "",
      regex_pattern: field.regex_pattern || field.pattern || "",
    });
  };

  const handleCancelEdit = () => {
    setEditingField(null);
    setEditValues({ context_label: "", regex_pattern: "" });
  };

  const handleSaveEdit = async (fieldName: string) => {
    if (!config) return;

    try {
      const oldPattern = config.fields[fieldName].regex_pattern;
      const newPattern = editValues.regex_pattern;

      // Update local config
      const updatedConfig = { ...config };
      const field = updatedConfig.fields[fieldName];
      
      // Update first location's context label if locations exist
      if (field.locations && field.locations.length > 0) {
        field.locations[0].context = {
          ...field.locations[0].context,
          label: editValues.context_label,
        };
      }
      
      // Update regex pattern
      field.regex_pattern = newPattern;
      
      updatedConfig.fields[fieldName] = field;

      setConfig(updatedConfig);
      setEditingField(null);

      // Learn pattern in backend (adaptive learning)
      if (oldPattern !== newPattern) {
        // TODO: Implement pattern learning API
        // await learningAPI.learnPattern({
        //   field_name: fieldName,
        //   regex_pattern: newPattern
        // });
        console.log("Pattern updated:", { fieldName, oldPattern, newPattern });
      }
    } catch (err) {
      console.error("Error saving field:", err);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-96 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!config) {
    return null;
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Preview Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Preview Template</CardTitle>
              <CardDescription>
                Klik pada field untuk highlight di preview
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setImageKey((prev) => prev + 1)}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Page Navigation */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mb-4 p-3 bg-muted/50 rounded-lg">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setCurrentPage((p) => Math.max(1, p - 1));
                  setImageKey((prev) => prev + 1);
                }}
                disabled={currentPage === 1 || loadingPages}
              >
                <ChevronLeft className="h-4 w-4 mr-1" />
                Previous
              </Button>

              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">
                  Page {currentPage} of {totalPages}
                </span>
                {loadingPages && (
                  <RefreshCw className="h-3 w-3 animate-spin text-muted-foreground" />
                )}
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setCurrentPage((p) => Math.min(totalPages, p + 1));
                  setImageKey((prev) => prev + 1);
                }}
                disabled={currentPage === totalPages || loadingPages}
              >
                Next
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          )}

          <div className="relative overflow-auto border rounded-lg bg-muted/30">
            <Image
              src={getImageUrl()}
              alt={`Template Preview - Page ${currentPage}`}
              className="w-full h-auto"
              width={100}
              height={100}
            />
          </div>
        </CardContent>
      </Card>

      {/* Fields List with Page Tabs */}
      <Card>
        <CardHeader>
          <CardTitle>Daftar Field ({config.metadata.field_count})</CardTitle>
          <CardDescription>
            Klik field untuk highlight di preview
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs
            value={currentPage.toString()}
            onValueChange={handlePageTabChange}
            className="justify-center items-center"
          >
            <TabsList
              className="grid w-full"
              style={{ gridTemplateColumns: `repeat(${totalPages}, 1fr)` }}
            >
              {/* scroll area auto height */}
              {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                (page) => {
                  const fieldsOnPage = getFieldsByPage()[page] || [];
                  return (
                    <TabsTrigger key={page} value={page.toString()}>
                      Page {page}
                      <Badge className="text-xs" variant="destructive">{fieldsOnPage.length}</Badge>
                    </TabsTrigger>
                  );
                }
              )}
            </TabsList>

            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
              const fieldsOnPage = getFieldsByPage()[page] || [];

              return (
                <ScrollArea
                  className={`h-[calc(140vh-20rem)] max-h-[calc(140vh-20rem)] w-full rounded-md border px-4 ${
                    page === currentPage ? "" : "hidden"
                  }`}
                  key={page}
                >
                  <TabsContent
                    key={page}
                    value={page.toString()}
                    className="mt-4"
                  >
                    {fieldsOnPage.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        No fields on this page
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {fieldsOnPage.map(([fieldName, field]) => {
                          const isEditing = editingField === fieldName;

                          return (
                            <div
                              key={fieldName}
                              className={`p-4 border rounded-lg transition-colors ${
                                selectedField === fieldName
                                  ? "border-red-500 bg-red-50 dark:bg-red-950"
                                  : "border-border hover:border-primary"
                              }`}
                            >
                              <div className="flex items-start justify-between gap-4">
                                <div
                                  className="flex-1 cursor-pointer"
                                  onClick={() =>
                                    !isEditing && handleFieldClick(fieldName)
                                  }
                                >
                                  <div className="flex items-center gap-2 mb-2">
                                    <h4 className="font-semibold">
                                      {fieldName}
                                    </h4>
                                    {field.extraction_strategy && (
                                      <Badge
                                        variant={
                                          selectedField === fieldName
                                            ? "destructive"
                                            : "default"
                                        }
                                      >
                                        {field.extraction_strategy}
                                      </Badge>
                                    )}
                                  </div>

                                  {isEditing ? (
                                    <div className="space-y-3 mt-3">
                                      <div>
                                        <Label
                                          htmlFor={`label-${fieldName}`}
                                          className="text-sm font-medium"
                                        >
                                          Context Label
                                        </Label>
                                        <Input
                                          id={`label-${fieldName}`}
                                          value={editValues.context_label}
                                          onChange={(e) =>
                                            setEditValues({
                                              ...editValues,
                                              context_label: e.target.value,
                                            })
                                          }
                                          className="mt-1"
                                          placeholder="e.g., Nama:"
                                        />
                                      </div>
                                      <div>
                                        <Label
                                          htmlFor={`pattern-${fieldName}`}
                                          className="text-sm font-medium"
                                        >
                                          Regex Pattern
                                        </Label>
                                        <Input
                                          id={`pattern-${fieldName}`}
                                          value={editValues.regex_pattern}
                                          onChange={(e) =>
                                            setEditValues({
                                              ...editValues,
                                              regex_pattern: e.target.value,
                                            })
                                          }
                                          className="mt-1 font-mono text-xs"
                                          placeholder="e.g., [A-Za-z\\s]+"
                                        />
                                      </div>
                                      <div className="text-sm text-muted-foreground">
                                        {field.marker_text && (
                                          <p>
                                            <span className="font-medium">
                                              Marker:
                                            </span>{" "}
                                            {field.marker_text}
                                          </p>
                                        )}
                                        {(() => {
                                          const locations = getFieldLocations(field);
                                          const firstLocation = locations[0];
                                          if (!firstLocation) return null;
                                          return (
                                            <p className="font-mono text-xs">
                                              <span className="font-medium">
                                                Posisi:
                                              </span>{" "}
                                              ({Math.round(firstLocation.x0)},{" "}
                                              {Math.round(firstLocation.y0)}) - (
                                              {Math.round(firstLocation.x1)},{" "}
                                              {Math.round(firstLocation.y1)})
                                            </p>
                                          );
                                        })()}
                                      </div>
                                    </div>
                                  ) : (
                                    <div className="text-sm text-muted-foreground space-y-1">
                                      {(() => {
                                        const locations = getFieldLocations(field);
                                        const locationCount = getLocationCount(field);
                                        const firstLocation = locations[0];
                                        
                                        return (
                                          <>
                                            {locationCount > 1 && (
                                              <div className="flex items-center gap-2 mb-2">
                                                <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-1 text-xs font-medium text-blue-700">
                                                  {locationCount} lokasi
                                                </span>
                                              </div>
                                            )}
                                            {firstLocation?.context?.label && (
                                              <p>
                                                <span className="font-medium">
                                                  Label:
                                                </span>{" "}
                                                {firstLocation.context.label}
                                              </p>
                                            )}
                                            {field.marker_text && (
                                              <p>
                                                <span className="font-medium">
                                                  Marker:
                                                </span>{" "}
                                                {field.marker_text}
                                              </p>
                                            )}
                                            {(field.regex_pattern || field.pattern) && (
                                              <p className="font-mono text-xs bg-muted px-2 py-1 rounded">
                                                <span className="font-medium">
                                                  Pattern:
                                                </span>{" "}
                                                {field.regex_pattern || field.pattern}
                                              </p>
                                            )}
                                            {firstLocation && (
                                              <p className="font-mono text-xs">
                                                <span className="font-medium">
                                                  Posisi:
                                                </span>{" "}
                                                ({Math.round(firstLocation.x0)},{" "}
                                                {Math.round(firstLocation.y0)}) - (
                                                {Math.round(firstLocation.x1)},{" "}
                                                {Math.round(firstLocation.y1)})
                                                {locationCount > 1 && (
                                                  <span className="text-muted-foreground ml-1">
                                                    (lokasi 1 dari {locationCount})
                                                  </span>
                                                )}
                                              </p>
                                            )}
                                          </>
                                        );
                                      })()}
                                    </div>
                                  )}
                                </div>

                                <div className="flex gap-1">
                                  {isEditing ? (
                                    <>
                                      <Button
                                        size="icon"
                                        variant="ghost"
                                        onClick={() =>
                                          handleSaveEdit(fieldName)
                                        }
                                        title="Save"
                                      >
                                        <Save className="h-4 w-4" />
                                      </Button>
                                      <Button
                                        size="icon"
                                        variant="ghost"
                                        onClick={handleCancelEdit}
                                        title="Cancel"
                                      >
                                        <X className="h-4 w-4" />
                                      </Button>
                                    </>
                                  ) : (
                                    <Button
                                      size="icon"
                                      variant="ghost"
                                      onClick={() =>
                                        handleEditField(fieldName, field)
                                      }
                                      title="Edit"
                                    >
                                      <Edit2 className="h-4 w-4" />
                                    </Button>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </TabsContent>
                </ScrollArea>
              );
            })}
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
