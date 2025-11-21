"use client";

import { Progress } from "@/components/ui/progress";
import type { OverviewMetrics } from "@/lib/types/dashboard.types";

interface PerformanceMetricsProps {
  overview: OverviewMetrics;
}

export function PerformanceMetrics({ overview }: PerformanceMetricsProps) {
  const metrics = [
    {
      label: "Overall Accuracy",
      value: (overview.overall_accuracy * 100).toFixed(1) + "%",
      progress: overview.overall_accuracy * 100,
      description: "Average extraction accuracy across all fields",
    },
    {
      label: "Validation Rate",
      value: (overview.validation_rate * 100).toFixed(1) + "%",
      progress: overview.validation_rate * 100,
      description: "Percentage of documents validated by users",
    },
    {
      label: "Corrections Made",
      value: overview.total_corrections.toString(),
      progress: Math.min((overview.total_corrections / overview.total_documents) * 10, 100),
      description: "Total number of user corrections",
    },
  ];

  return (
    <div className="space-y-4">
      {metrics.map((metric, index) => (
        <div key={index} className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">{metric.label}</span>
            <span className="text-2xl font-bold">{metric.value}</span>
          </div>
          <Progress value={metric.progress} className="h-2" />
          <p className="text-xs text-muted-foreground">{metric.description}</p>
        </div>
      ))}
    </div>
  );
}
