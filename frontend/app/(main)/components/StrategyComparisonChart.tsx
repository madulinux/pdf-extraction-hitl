"use client";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip as UITooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { StrategyComparison } from "@/lib/api/dashboard.api";
import { HelpCircle } from "lucide-react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  ResponsiveContainer,
  Tooltip as ChartTooltip,
} from "recharts";

interface StrategyComparisonChartProps {
  strategies: StrategyComparison[];
}

export function StrategyComparisonChart({
  strategies,
}: StrategyComparisonChartProps) {
  // Prepare data for radar chart
  const radarData = [
    {
      metric: "Accuracy",
      "Rule-Based":
        (strategies.find((s) => s.strategy === "rule_based")?.avg_accuracy ||
          0) * 100,
      CRF:
        (strategies.find((s) => s.strategy === "crf")?.avg_accuracy || 0) * 100,
    },
    {
      metric: "Confidence",
      "Rule-Based":
        (strategies.find((s) => s.strategy === "rule_based")?.avg_confidence ||
          0) * 100,
      CRF:
        (strategies.find((s) => s.strategy === "crf")?.avg_confidence || 0) *
        100,
    },
    {
      metric: "High Accuracy Rate",
      "Rule-Based":
        (strategies.find((s) => s.strategy === "rule_based")
          ?.high_accuracy_rate || 0) * 100,
      CRF:
        (strategies.find((s) => s.strategy === "crf")?.high_accuracy_rate ||
          0) * 100,
    },
    {
      metric: "Effectiveness",
      "Rule-Based":
        (strategies.find((s) => s.strategy === "rule_based")
          ?.effectiveness_score || 0) * 100,
      CRF:
        (strategies.find((s) => s.strategy === "crf")?.effectiveness_score ||
          0) * 100,
    },
  ];

  const getStrategyLabel = (strategy: string) => {
    return strategy === "rule_based" ? "Rule-Based" : "CRF";
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Hybrid Architecture Performance</CardTitle>
          <TooltipProvider>
            <UITooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent className="max-w-sm">
                <p className="text-sm">
                  Compares the performance of Rule-Based (deterministic, transparent)
                  and CRF (probabilistic, adaptive) extraction strategies. The radar
                  chart visualizes accuracy, confidence, high accuracy rate, and
                  effectiveness score. Balanced scores validate the hybrid architecture
                  with confidence-based strategy selection.
                </p>
              </TooltipContent>
            </UITooltip>
          </TooltipProvider>
        </div>
        <CardDescription>
          Rule-Based vs CRF strategy comparison (Tujuan #1)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Radar Chart */}
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="metric" tick={{ fontSize: 12 }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} />
              <Radar
                name="Rule-Based"
                dataKey="Rule-Based"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.3}
              />
              <Radar
                name="CRF"
                dataKey="CRF"
                stroke="#10b981"
                fill="#10b981"
                fillOpacity={0.3}
              />
              <Legend />
              <ChartTooltip />
            </RadarChart>
          </ResponsiveContainer>

          {/* Strategy Details */}
          <div className="grid grid-cols-2 gap-4">
            {strategies.map((strategy) => (
              <div
                key={strategy.strategy}
                className="p-4 border rounded-lg space-y-3"
              >
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold">
                    {getStrategyLabel(strategy.strategy)}
                  </h4>
                  <Badge
                    variant={
                      strategy.strategy === "rule_based" ? "default" : "secondary"
                    }
                  >
                    {strategy.usage_count} uses
                  </Badge>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Accuracy:</span>
                    <span className="font-medium">
                      {(strategy.avg_accuracy * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Confidence:</span>
                    <span className="font-medium">
                      {(strategy.avg_confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">
                      High Accuracy:
                    </span>
                    <span className="font-medium">
                      {(strategy.high_accuracy_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between pt-2 border-t">
                    <span className="text-muted-foreground font-medium">
                      Effectiveness:
                    </span>
                    <span className="font-bold text-primary">
                      {(strategy.effectiveness_score * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Insight */}
          <div className="p-3 bg-muted/50 rounded-lg">
            <p className="text-xs text-muted-foreground">
              <strong>Insight:</strong> Balanced effectiveness scores validate
              the hybrid architecture with confidence-based selection mechanism.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
