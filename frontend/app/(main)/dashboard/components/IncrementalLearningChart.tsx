import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { TrendingUp, Package } from "lucide-react";
import { IncrementalLearning } from "@/lib/types/dashboard.types";

interface IncrementalLearningChartProps {
  data: IncrementalLearning;
}

export function IncrementalLearningChart({
  data,
}: IncrementalLearningChartProps) {
  // Prepare chart data
  const chartData = data.batches.map((batch) => ({
    batch: `Batch ${batch.batch_number}`,
    batchNumber: batch.batch_number,
    before: (batch.accuracy_before * 100).toFixed(2),
    after: (batch.accuracy_after * 100).toFixed(2),
    improvement: (batch.improvement * 100).toFixed(2),
    efficiency: (batch.learning_efficiency * 100).toFixed(2),
    feedback: batch.feedback_count,
    range: batch.document_range,
  }));

  // Use best batch from summary (based on learning efficiency)
  const bestBatchNumber = data.summary.best_batch_number || 1;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              Incremental Learning Progress
            </CardTitle>
            <CardDescription>
              Accuracy improvement across batches of{" "}
              {data.summary.batch_size_used} documents
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Badge variant="outline">
              {data.summary.total_batches} Batches
            </Badge>
            <Badge variant="default">
              +{(data.summary.total_improvement * 100).toFixed(2)}% Total
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">
                {data.summary.total_batches}
              </p>
              <p className="text-xs text-muted-foreground">Total Batches</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">
                +{(data.summary.avg_improvement_per_batch * 100).toFixed(2)}%
              </p>
              <p className="text-xs text-muted-foreground">Avg per Batch</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-600">
                {data.summary.batch_size_used}
              </p>
              <p className="text-xs text-muted-foreground">Batch Size</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-orange-600">
                Batch {bestBatchNumber}
              </p>
              <p className="text-xs text-muted-foreground">Best Efficiency</p>
            </div>
          </div>

          {/* Chart */}
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="batch" tick={{ fontSize: 12 }} />
                <YAxis
                  label={{
                    value: "Accuracy (%)",
                    angle: -90,
                    position: "insideLeft",
                  }}
                  domain={[0, 100]}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-background border rounded-lg p-3 shadow-lg">
                          <p className="font-semibold mb-2">{data.batch}</p>
                          <div className="space-y-1 text-sm">
                            <p className="text-muted-foreground">
                              Documents: {data.range}
                            </p>
                            <p className="text-blue-600">
                              Before: {data.before}%
                            </p>
                            <p className="text-green-600">
                              After: {data.after}%
                            </p>
                            <p className="font-semibold text-orange-600">
                              Improvement: +{data.improvement}%
                            </p>
                            <p className="text-muted-foreground">
                              Feedback: {data.feedback}
                            </p>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="before"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Before"
                  dot={{ r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="after"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="After"
                  dot={{ r: 4 }}
                />
                <ReferenceLine
                  y={90}
                  stroke="#ef4444"
                  strokeDasharray="3 3"
                  label={{ value: "Target: 90%", position: "right" }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Insights */}
          <div className="grid grid-cols-2 gap-4 pt-4 border-t">
            <div className="flex items-start gap-2">
              <TrendingUp className="h-4 w-4 text-green-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium">Learning Trend</p>
                <p className="text-xs text-muted-foreground">
                  {data.summary.avg_improvement_per_batch > 0.05
                    ? "Strong improvement with each batch"
                    : data.summary.avg_improvement_per_batch > 0.02
                    ? "Steady improvement observed"
                    : "Approaching convergence"}
                </p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Package className="h-4 w-4 text-blue-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium">Batch Strategy</p>
                <p className="text-xs text-muted-foreground">
                  Optimal batch size: {data.summary.optimal_batch_size}{" "}
                  documents
                </p>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
