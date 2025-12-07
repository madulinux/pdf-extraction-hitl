"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, CheckCircle2 } from "lucide-react";
import { TemplateSummary } from "@/lib/api/dashboard.api";

interface TemplateCardProps {
  template: TemplateSummary;
}

export function TemplateCard({ template }: TemplateCardProps) {

  const getTemplateIcon = (type: string) => {
    switch (type) {
      case "form":
        return "📋";
      case "table":
        return "📊";
      case "letter":
        return "✉️";
      case "mixed":
        return "📑";
      default:
        return "📄";
    }
  };

  const getStatusColor = (status: string) => {
    return status === "active" ? "default" : "secondary";
  };

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 0.95) return "text-green-600";
    if (accuracy >= 0.85) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{getTemplateIcon(template.type)}</span>
          <div>
            <CardTitle className="text-lg">{template.name}</CardTitle>
            <p className="text-xs text-muted-foreground capitalize">
              {template.type} Template
            </p>
          </div>
        </div>
        <Badge variant={getStatusColor(template.status)}>
          {template.status}
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {/* Documents & Feedback */}
          <div className="grid grid-cols-2 gap-3">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Documents</p>
                <p className="text-lg font-bold">{template.documents}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Validated</p>
                <p className="text-lg font-bold">{template.validated}</p>
              </div>
            </div>
          </div>

          {/* Accuracy - PRIMARY METRIC */}
          <div className="p-3 bg-primary/10 rounded-lg border-2 border-primary/20">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium">Accuracy</span>
                <p className="text-xs text-muted-foreground">HITL Metric</p>
              </div>
              <span className={`text-2xl font-bold ${getAccuracyColor(template.accuracy)}`}>
                {(template.accuracy * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          {/* Feedback & Total Fields */}
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="flex flex-col">
              <span className="text-muted-foreground text-xs">Feedback Received</span>
              <span className="font-bold text-lg">{template.feedback_count}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-muted-foreground text-xs">Total Fields</span>
              <span className="font-medium text-lg">{template.field_count}</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
