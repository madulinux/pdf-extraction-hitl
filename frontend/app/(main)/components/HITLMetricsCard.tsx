"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { HITLLearningMetrics } from "@/lib/api/dashboard.api";
import { TrendingUp, Target, Zap, HelpCircle } from "lucide-react";

interface HITLMetricsCardProps {
  metrics: HITLLearningMetrics;
}

export function HITLMetricsCard({ metrics }: HITLMetricsCardProps) {
  const getEfficiencyColor = (efficiency: number) => {
    if (efficiency >= 0.02) return "text-green-600";
    if (efficiency >= 0.01) return "text-yellow-600";
    return "text-orange-600";
  };

  const getUtilizationColor = (rate: number) => {
    if (rate >= 0.8) return "text-green-600";
    if (rate >= 0.6) return "text-yellow-600";
    return "text-orange-600";
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" />
            HITL Learning Efficiency
          </CardTitle>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent className="max-w-sm">
                <p className="text-sm">
                  Measures how effectively the system learns from user corrections.
                  Learning efficiency shows the average accuracy improvement per feedback,
                  while feedback utilization indicates the percentage of corrections
                  successfully converted into training data for model improvement.
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        <CardDescription>
          Adaptive learning performance metrics (Tujuan #2 & #3)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Learning Efficiency */}
          <div className="p-4 bg-muted/50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">Learning Efficiency</span>
              </div>
              <Badge variant="outline">
                {(metrics.learning_efficiency * 100).toFixed(2)}%
              </Badge>
            </div>
            <div className="flex items-baseline gap-2">
              <span
                className={`text-3xl font-bold ${getEfficiencyColor(
                  metrics.learning_efficiency
                )}`}
              >
                {metrics.avg_improvement_per_feedback.toFixed(2)}%
              </span>
              <span className="text-sm text-muted-foreground">
                improvement per feedback
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Average accuracy improvement per user correction
            </p>
          </div>

          {/* Feedback Utilization */}
          <div className="p-4 bg-muted/50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Target className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">Feedback Utilization</span>
              </div>
              <Badge variant="outline">
                {metrics.feedback_used_for_training} / {metrics.total_feedback}
              </Badge>
            </div>
            <div className="flex items-baseline gap-2">
              <span
                className={`text-3xl font-bold ${getUtilizationColor(
                  metrics.feedback_utilization_rate
                )}`}
              >
                {(metrics.feedback_utilization_rate * 100).toFixed(1)}%
              </span>
              <span className="text-sm text-muted-foreground">utilized</span>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Percentage of feedback converted to training data
            </p>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-2 gap-3 pt-2">
            <div className="text-center p-3 bg-background rounded-lg border">
              <p className="text-2xl font-bold text-primary">
                {metrics.total_feedback}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Total Feedback
              </p>
            </div>
            <div className="text-center p-3 bg-background rounded-lg border">
              <p className="text-2xl font-bold text-primary">
                {metrics.feedback_used_for_training}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Used for Training
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
