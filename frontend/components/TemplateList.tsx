"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { FileText, Calendar, Hash, Loader2, Eye } from "lucide-react";
import { templatesAPI } from "@/lib/api/templates.api";
import { Template } from "@/lib/types/template.types";
import { formatDate } from "@/lib/utils";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "./ui/input";

interface TemplateListProps {
  onSelectTemplate?: (template: Template) => void;
  refreshTrigger?: number;
  showDetailButton?: boolean;
}

export default function TemplateList({
  onSelectTemplate,
  refreshTrigger,
  showDetailButton = false,
}: TemplateListProps) {
  const router = useRouter();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [search, setSearch] = useState("");

  const loadTemplates = async (search?: string) => {
    setLoading(true);
    setError("");
    try {
      const result = await templatesAPI.list(search, 1, 10, selectedId);
      setTemplates(result.templates);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Gagal memuat template";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTemplates();
  }, [refreshTrigger]);

  const handleSelect = (template: Template) => {
    setSelectedId(template.id);
    if (onSelectTemplate) {
      onSelectTemplate(template);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-6">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Daftar Template</CardTitle>
        <CardDescription>
          Pilih template untuk melakukan ekstraksi data
        </CardDescription>
      </CardHeader>
      <CardContent>
        {templates.length === 0 ? (
          <p className="text-muted-foreground text-center py-8">
            Belum ada template. Silakan upload template terlebih dahulu.
          </p>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Input
                type="text"
                placeholder="Cari template..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            {templates.map((template) => (
              <div
                key={template.id}
                onClick={() => handleSelect(template)}
                className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                  selectedId === template.id
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/50"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg flex items-center gap-2">
                      <FileText className="w-5 h-5 text-primary" />
                      {template.name}
                    </h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      {template.filename}
                    </p>

                    <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Hash className="w-4 h-4" />
                        {template.field_count} field
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        {formatDate(template.created_at)}
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-2">
                    <Badge
                      variant={
                        template.status === "active" ? "default" : "secondary"
                      }
                    >
                      {template.status}
                    </Badge>
                    {showDetailButton && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/templates/${template.id}`);
                        }}
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        Detail
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
