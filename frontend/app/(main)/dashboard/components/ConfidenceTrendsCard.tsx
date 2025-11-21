"use client";

import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import type { ConfidenceTrends } from "@/lib/types/dashboard.types";
import { Brain, FileCode, MapPin, TrendingUp } from "lucide-react";

interface ConfidenceTrendsCardProps {
  data: ConfidenceTrends;
}

const strategyIcons: Record<string, React.ReactNode> = {
  crf: <Brain className="h-4 w-4" />,
  rule_based: <FileCode className="h-4 w-4" />,
  position_based: <MapPin className="h-4 w-4" />,
};

const strategyLabels: Record<string, string> = {
  crf: "CRF",
  rule_based: "Rule-Based",
  position_based: "Position-Based",
};

export function ConfidenceTrendsCard({ data }: ConfidenceTrendsCardProps) {
  if (!data || !data.by_strategy) {
    return (
      <div className="text-center text-muted-foreground py-8">
        No confidence data available
      </div>
    );
  }

  const avgConfidence = data.avg_confidence * 100;

  // Detect overconfident strategies (confidence >> accuracy)
  const getCalibrationStatus = (confidence: number) => {
    if (confidence > 0.85) return { label: "High", variant: "default" as const };
    if (confidence > 0.6) return { label: "Medium", variant: "secondary" as const };
    return { label: "Low", variant: "outline" as const };
  };

  return (
    <div className="space-y-6">
      {/* Overall Confidence */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Overall Confidence</span>
          </div>
          <span className="text-2xl font-bold">{avgConfidence.toFixed(1)}%</span>
        </div>
        <Progress value={avgConfidence} className="h-2" />
      </div>

      {/* By Strategy */}
      <div className="space-y-4">
        <p className="text-sm font-medium text-muted-foreground">
          Confidence by Strategy:
        </p>

        {Object.entries(data.by_strategy)
          .sort(([, a], [, b]) => b.avg_confidence - a.avg_confidence)
          .map(([strategy, stats]) => {
            const confidence = stats.avg_confidence * 100;
            const calibration = getCalibrationStatus(stats.avg_confidence);

            return (
              <div key={strategy} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {strategyIcons[strategy]}
                    <span className="text-sm font-medium">
                      {strategyLabels[strategy] || strategy}
                    </span>
                    <Badge variant={calibration.variant} className="text-xs">
                      {calibration.label}
                    </Badge>
                  </div>
                  <span className="text-lg font-bold">
                    {confidence.toFixed(1)}%
                  </span>
                </div>

                <Progress value={confidence} className="h-1.5" />

                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    Range: {(stats.min_confidence * 100).toFixed(0)}% -{" "}
                    {(stats.max_confidence * 100).toFixed(0)}%
                  </span>
                  <span>{stats.sample_count.toLocaleString()} samples</span>
                </div>
              </div>
            );
          })}
      </div>

      {/* Interpretation */}
      <div className="bg-muted/50 rounded-lg p-4">
        <p className="text-xs text-muted-foreground">
          <span className="font-semibold text-foreground">💡 Note:</span>{" "}
          Confidence scores indicate how certain the model is about its
          predictions. Higher confidence generally correlates with higher
          accuracy, but watch for overconfident strategies.
        </p>
      </div>
    </div>
  );
}
