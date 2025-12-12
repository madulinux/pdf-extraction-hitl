"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Clock, TrendingDown, TrendingUp, Minus } from "lucide-react";
import type { TimeTrends } from "@/lib/types/dashboard.types";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface TimeTrendsChartProps {
  data: TimeTrends;
}

export function TimeTrendsChart({ data }: TimeTrendsChartProps) {
  if (!data || data.trend_data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Extraction Time Trends
          </CardTitle>
          <CardDescription>
            Track extraction speed over time
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <Clock className="h-12 w-12 mb-4 opacity-50" />
            <p className="text-sm">No time trend data available</p>
            <p className="text-xs mt-2">Process more documents to see trends</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Prepare chart data
  const chartData = data.trend_data.map((point) => ({
    document: point.document_number,
    time: point.extraction_time_ms,
    movingAvg: point.moving_average,
  }));

  // Determine performance trend
  const getTrendIndicator = () => {
    if (data.performance_change < -5) {
      return {
        icon: TrendingDown,
        color: "text-green-600",
        bg: "bg-green-500",
        label: "Improving",
        description: "Getting faster",
      };
    } else if (data.performance_change > 5) {
      return {
        icon: TrendingUp,
        color: "text-red-600",
        bg: "bg-red-500",
        label: "Degrading",
        description: "Getting slower",
      };
    } else {
      return {
        icon: Minus,
        color: "text-gray-600",
        bg: "bg-gray-500",
        label: "Stable",
        description: "Consistent",
      };
    }
  };

  const trend = getTrendIndicator();
  const TrendIcon = trend.icon;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Extraction Time Trends
        </CardTitle>
        <CardDescription>
          Track how extraction speed changes over {data.total_documents} documents
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2 p-3 rounded-lg border bg-card">
            <p className="text-xs text-muted-foreground">First 10 Documents</p>
            <div className="flex items-baseline gap-2">
              <p className="text-2xl font-bold">{data.avg_time_first_10.toFixed(1)}</p>
              <span className="text-xs text-muted-foreground">ms avg</span>
            </div>
          </div>

          <div className="space-y-2 p-3 rounded-lg border bg-card">
            <p className="text-xs text-muted-foreground">Last 10 Documents</p>
            <div className="flex items-baseline gap-2">
              <p className="text-2xl font-bold">{data.avg_time_last_10.toFixed(1)}</p>
              <span className="text-xs text-muted-foreground">ms avg</span>
            </div>
          </div>

          <div className="space-y-2 p-3 rounded-lg border bg-card">
            <p className="text-xs text-muted-foreground">Performance Trend</p>
            <div className="flex items-center gap-2">
              <p className={`text-2xl font-bold ${trend.color}`}>
                {data.performance_change > 0 ? '+' : ''}
                {data.performance_change.toFixed(1)}%
              </p>
              <Badge className={trend.bg}>
                <TrendIcon className="h-3 w-3 mr-1" />
                {trend.label}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">{trend.description}</p>
          </div>
        </div>

        {/* Chart */}
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="document"
                label={{ value: "Document Number", position: "insideBottom", offset: -5 }}
                className="text-xs"
              />
              <YAxis
                label={{ value: "Time (ms)", angle: -90, position: "insideLeft" }}
                className="text-xs"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "var(--radius)",
                }}
                labelFormatter={(value) => `Document #${value}`}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="time"
                
                stroke="#0b3f94ff"
                strokeWidth={1}
                dot={{ r: 2 }}
                name="Extraction Time"
                opacity={0.5}
                />
              <Line
                type="monotone"
                dataKey="movingAvg"
                stroke="#e2aa0eff"
                strokeWidth={2}
                dot={false}
                name="Moving Average (5 docs)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Insights */}
        <div className="p-4 rounded-lg bg-muted/50 space-y-2">
          <h4 className="text-sm font-semibold flex items-center gap-2">
            <TrendIcon className="h-4 w-4" />
            Performance Analysis
          </h4>
          <ul className="text-sm space-y-1 text-muted-foreground">
            {data.performance_change < -5 && (
              <li>✅ Performance is improving - extraction is getting faster over time</li>
            )}
            {data.performance_change > 5 && (
              <li>⚠️ Performance is degrading - extraction is getting slower (may need optimization)</li>
            )}
            {Math.abs(data.performance_change) <= 5 && (
              <li>✅ Performance is stable - consistent extraction speed</li>
            )}
            <li>
              📊 Analyzed {data.total_documents} documents with timing data
            </li>
            <li>
              📈 Average change: {data.performance_change > 0 ? '+' : ''}
              {data.performance_change.toFixed(1)}% from first 10 to last 10 documents
            </li>
            {data.avg_time_last_10 < data.avg_time_first_10 && (
              <li>
                ⚡ Speed improvement: {(data.avg_time_first_10 - data.avg_time_last_10).toFixed(1)}ms faster
              </li>
            )}
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
