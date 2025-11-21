"use client";

import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import type { StrategyPerformance } from "@/lib/types/dashboard.types";
import { Brain, FileCode, MapPin } from "lucide-react";

interface StrategyPerformanceTableProps {
  data: Record<string, StrategyPerformance>;
}

const strategyIcons: Record<string, React.ReactNode> = {
  crf: <Brain className="h-4 w-4" />,
  rule_based: <FileCode className="h-4 w-4" />,
  position_based: <MapPin className="h-4 w-4" />,
};

const strategyLabels: Record<string, string> = {
  crf: "CRF (Machine Learning)",
  rule_based: "Rule-Based",
  position_based: "Position-Based",
};

export function StrategyPerformanceTable({
  data,
}: StrategyPerformanceTableProps) {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        No strategy performance data available
      </div>
    );
  }

  // Sort strategies by accuracy
  const sortedStrategies = Object.entries(data).sort(
    ([, a], [, b]) => b.overall_accuracy - a.overall_accuracy
  );

  return (
    <div className="space-y-6">
      {sortedStrategies.map(([strategy, performance], index) => {
        const accuracy = performance.overall_accuracy * 100;
        const isTopPerformer = index === 0;

        return (
          <div key={strategy} className="space-y-3">
            {/* Strategy Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {strategyIcons[strategy]}
                <h3 className="font-semibold">
                  {strategyLabels[strategy] || strategy}
                </h3>
                {isTopPerformer && (
                  <Badge variant="default">Best Performer</Badge>
                )}
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold">{accuracy.toFixed(1)}%</p>
                <p className="text-xs text-muted-foreground">
                  {performance.total_correct.toLocaleString()} /{" "}
                  {performance.total_attempts.toLocaleString()} attempts
                </p>
              </div>
            </div>

            {/* Progress Bar */}
            <Progress value={accuracy} className="h-2" />

            {/* Top Fields */}
            {performance.fields && Object.keys(performance.fields).length > 0 && (
              <div className="bg-muted/50 rounded-lg p-3">
                <p className="text-xs font-medium text-muted-foreground mb-2">
                  Top Performing Fields:
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(performance.fields)
                    .sort(([, a], [, b]) => b.accuracy - a.accuracy)
                    .slice(0, 4)
                    .map(([field, stats]) => (
                      <div
                        key={field}
                        className="flex items-center justify-between text-xs"
                      >
                        <span className="capitalize truncate">
                          {field.replace(/_/g, " ")}
                        </span>
                        <Badge variant="secondary" className="text-xs">
                          {(stats.accuracy * 100).toFixed(0)}%
                        </Badge>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
