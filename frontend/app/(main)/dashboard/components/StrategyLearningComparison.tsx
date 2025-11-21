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
import type { StrategyPerformance } from "@/lib/types/dashboard.types";
import { Brain, FileCode, MapPin } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface StrategyLearningComparisonProps {
  strategyPerformance: Record<string, StrategyPerformance>;
  accuracyOverTime: any[]; // We'll need to enhance this with strategy info
}

const strategyConfig = {
  crf: {
    label: "CRF (ML)",
    color: "hsl(var(--chart-1))",
    icon: <Brain className="h-4 w-4" />,
  },
  rule_based: {
    label: "Rule-Based",
    color: "hsl(var(--chart-2))",
    icon: <FileCode className="h-4 w-4" />,
  },
  position_based: {
    label: "Position-Based",
    color: "hsl(var(--chart-3))",
    icon: <MapPin className="h-4 w-4" />,
  },
};

export function StrategyLearningComparison({
  strategyPerformance,
}: StrategyLearningComparisonProps) {
  if (!strategyPerformance || Object.keys(strategyPerformance).length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        No strategy comparison data available
      </div>
    );
  }

  // Calculate improvement potential for each strategy
  const strategyStats = Object.entries(strategyPerformance).map(
    ([strategy, perf]) => {
      const accuracy = perf.overall_accuracy * 100;
      const successRate = perf.total_correct / perf.total_attempts;
      const potential = 100 - accuracy; // Room for improvement

      return {
        strategy,
        label: strategyConfig[strategy as keyof typeof strategyConfig]?.label || strategy,
        accuracy,
        attempts: perf.total_attempts,
        correct: perf.total_correct,
        successRate,
        potential,
        color: strategyConfig[strategy as keyof typeof strategyConfig]?.color,
      };
    }
  );

  // Sort by accuracy
  const sortedStats = strategyStats.sort((a, b) => b.accuracy - a.accuracy);

  // Prepare data for comparison chart
  const chartData = sortedStats.map((stat) => ({
    name: stat.label,
    accuracy: stat.accuracy,
    potential: stat.potential,
  }));

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        {sortedStats.map((stat, index) => {
          const config = strategyConfig[stat.strategy as keyof typeof strategyConfig];
          const isTopPerformer = index === 0;

          return (
            <div
              key={stat.strategy}
              className={`p-4 rounded-lg border ${
                isTopPerformer ? "border-primary bg-primary/5" : "border-border"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {config?.icon}
                  <span className="text-sm font-medium">{stat.label}</span>
                </div>
                {isTopPerformer && (
                  <Badge variant="default" className="text-xs">
                    Best
                  </Badge>
                )}
              </div>
              <p className="text-2xl font-bold">{stat.accuracy.toFixed(1)}%</p>
              <p className="text-xs text-muted-foreground mt-1">
                {stat.correct.toLocaleString()} / {stat.attempts.toLocaleString()} correct
              </p>
            </div>
          );
        })}
      </div>

      {/* Comparison Chart */}
      <div>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
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
                      <p className="text-lg font-bold text-primary">
                        {data.accuracy.toFixed(1)}% Accuracy
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {data.potential.toFixed(1)}% room for improvement
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
              dot={{ r: 6 }}
              name="Current Accuracy"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Insights */}
      <div className="bg-muted/50 rounded-lg p-4 space-y-3">
        <p className="text-sm font-semibold">📊 Strategy Comparison Insights:</p>
        <div className="space-y-2 text-sm text-muted-foreground">
          <p>
            • <span className="font-semibold text-foreground">{sortedStats[0].label}</span>{" "}
            is the top performer with {sortedStats[0].accuracy.toFixed(1)}% accuracy
          </p>
          <p>
            • <span className="font-semibold text-foreground">CRF (Machine Learning)</span>{" "}
            shows the best generalization capability across different field types
          </p>
          <p>
            • <span className="font-semibold text-foreground">Rule-Based</span>{" "}
            excels at pattern-matching fields (e.g., certificate numbers, dates)
          </p>
          <p>
            • <span className="font-semibold text-foreground">Position-Based</span>{" "}
            is reliable only for fixed-position fields in consistent layouts
          </p>
        </div>
      </div>

      {/* Learning Potential */}
      <div className="grid grid-cols-3 gap-4">
        {sortedStats.map((stat) => {
          const config = strategyConfig[stat.strategy as keyof typeof strategyConfig];
          const canImprove = stat.potential > 20;

          return (
            <div key={stat.strategy} className="text-center p-3 bg-muted/30 rounded-lg">
              <div className="flex items-center justify-center gap-2 mb-2">
                {config?.icon}
                <span className="text-xs font-medium">{stat.label}</span>
              </div>
              <p className="text-lg font-bold">
                {stat.potential.toFixed(1)}%
              </p>
              <p className="text-xs text-muted-foreground">
                {canImprove ? "High potential" : "Near optimal"}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
