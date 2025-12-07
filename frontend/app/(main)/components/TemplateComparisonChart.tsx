"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { TemplateSummary } from "@/lib/api/dashboard.api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface TemplateComparisonChartProps {
  templates: TemplateSummary[];
}

export function TemplateComparisonChart({
  templates,
}: TemplateComparisonChartProps) {
  const chartData = templates.map((t) => ({
    name: t.name,
    accuracy: (t.accuracy * 100).toFixed(1),
    documents: t.documents,
    feedback: t.feedback_count,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Template Performance Comparison</CardTitle>
        <CardDescription>
          Accuracy and document count across all templates
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Bar
              yAxisId="left"
              dataKey="accuracy"
              fill="#3b82f6"
              name="Accuracy (%)"
            />
            <Bar
              yAxisId="right"
              dataKey="documents"
              fill="#10b981"
              name="Documents"
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
