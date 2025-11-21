"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { LearningProgress } from "@/lib/types/dashboard.types";
import { TrendingUp, TrendingDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface LearningProgressChartProps {
  data: LearningProgress;
}

export function LearningProgressChart({ data }: LearningProgressChartProps) {
  if (!data || !data.batches || data.batches.length === 0) {
    return (
      <div className="flex items-center justify-center h-[300px] text-muted-foreground">
        No learning progress data available
      </div>
    );
  }

  const chartData = data.batches.map((batch) => ({
    name: `Batch ${batch.batch_number}`,
    accuracy: (batch.accuracy * 100).toFixed(1),
    docs: `${batch.start_doc}-${batch.end_doc}`,
  }));

  const isImproving = data.improvement_rate > 0;

  return (
    <div className="space-y-4">
      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">First Batch</p>
          <p className="text-2xl font-bold">
            {(data.first_batch_accuracy * 100).toFixed(1)}%
          </p>
        </div>
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">Last Batch</p>
          <p className="text-2xl font-bold">
            {(data.last_batch_accuracy * 100).toFixed(1)}%
          </p>
        </div>
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">Improvement</p>
          <div className="flex items-center gap-2">
            <p className="text-2xl font-bold">
              {data.improvement_rate.toFixed(1)}%
            </p>
            {isImproving ? (
              <Badge variant="default" className="gap-1">
                <TrendingUp className="h-3 w-3" />
                Growing
              </Badge>
            ) : (
              <Badge variant="destructive" className="gap-1">
                <TrendingDown className="h-3 w-3" />
                Declining
              </Badge>
            )}
          </div>
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" tick={{ fontSize: 12 }} />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 12 }}
            label={{ value: "Accuracy (%)", angle: -90, position: "insideLeft" }}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-background border rounded-lg p-3 shadow-lg">
                    <p className="font-semibold">{data.name}</p>
                    <p className="text-sm text-muted-foreground">
                      Documents: {data.docs}
                    </p>
                    <p className="text-lg font-bold text-primary mt-1">
                      {data.accuracy}% Accuracy
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="accuracy"
            stroke="hsl(var(--primary))"
            strokeWidth={3}
            dot={{ r: 5, fill: "hsl(var(--primary))" }}
            activeDot={{ r: 7 }}
            name="Accuracy (%)"
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Interpretation */}
      <div className="bg-muted/50 rounded-lg p-4">
        <p className="text-sm text-muted-foreground">
          {isImproving ? (
            <>
              <span className="font-semibold text-foreground">
                ✅ Adaptive Learning Working!
              </span>{" "}
              The model improved by {data.improvement_rate.toFixed(1)}% from the
              first batch ({(data.first_batch_accuracy * 100).toFixed(1)}%) to
              the last batch ({(data.last_batch_accuracy * 100).toFixed(1)}%),
              demonstrating effective learning from feedback.
            </>
          ) : (
            <>
              <span className="font-semibold text-foreground">
                ⚠️ No Improvement Detected
              </span>{" "}
              The model accuracy has not improved significantly. Consider
              reviewing the feedback quality or retraining the model.
            </>
          )}
        </p>
      </div>
    </div>
  );
}
