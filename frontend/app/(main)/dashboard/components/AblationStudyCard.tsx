"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { TrendingUp, Award, BarChart3 } from "lucide-react";
import type { AblationStudy } from "@/lib/types/dashboard.types";

interface AblationStudyCardProps {
  data: AblationStudy;
}

export function AblationStudyCard({ data }: AblationStudyCardProps) {
  if (!data || data.strategies.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Ablation Study
          </CardTitle>
          <CardDescription>
            Strategy performance comparison
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <BarChart3 className="h-12 w-12 mb-4 opacity-50" />
            <p className="text-sm">No strategy comparison data available</p>
            <p className="text-xs mt-2">Process more documents to see strategy analysis</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const improvementColor =
    data.improvement_over_best > 0
      ? "text-green-600"
      : data.improvement_over_best < 0
      ? "text-red-600"
      : "text-gray-600";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Ablation Study - Strategy Comparison
        </CardTitle>
        <CardDescription>
          Compare hybrid approach vs individual strategies
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Hybrid vs Best Single Strategy */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-lg bg-muted/50">
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">Hybrid Approach</p>
            <div className="flex items-baseline gap-2">
              <p className="text-3xl font-bold text-blue-600">
                {(data.hybrid_accuracy * 100).toFixed(1)}%
              </p>
              <Badge className="bg-blue-500">
                <Award className="h-3 w-3 mr-1" />
                Current
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              {data.hybrid_correct}/{data.hybrid_total} correct
            </p>
          </div>

          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">Best Single Strategy</p>
            <div className="flex items-baseline gap-2">
              <p className="text-3xl font-bold">
                {(data.best_single_accuracy * 100).toFixed(1)}%
              </p>
            </div>
            <p className="text-xs text-muted-foreground capitalize">
              {data.best_single_strategy?.replace('_', ' ')}
            </p>
          </div>

          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">Improvement</p>
            <div className="flex items-baseline gap-2">
              <p className={`text-3xl font-bold ${improvementColor}`}>
                {data.improvement_over_best > 0 ? '+' : ''}
                {data.improvement_over_best.toFixed(1)}%
              </p>
              {data.improvement_over_best > 0 && (
                <TrendingUp className="h-5 w-5 text-green-600" />
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              {data.improvement_over_best > 0
                ? 'Hybrid is better'
                : data.improvement_over_best < 0
                ? 'Single strategy better'
                : 'Equal performance'}
            </p>
          </div>
        </div>

        {/* Strategy Breakdown */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold">Individual Strategy Performance</h4>
          <div className="space-y-3">
            {data.strategies.map((strategy, index) => {
              const isBest = strategy.strategy === data.best_single_strategy;
              return (
                <div
                  key={strategy.strategy}
                  className={`p-3 rounded-lg border ${
                    isBest ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20' : 'bg-card'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Badge variant={isBest ? "default" : "outline"} className="capitalize">
                        {index + 1}. {strategy.strategy.replace('_', ' ')}
                      </Badge>
                      {isBest && (
                        <Badge className="bg-yellow-500">
                          <Award className="h-3 w-3 mr-1" />
                          Best Single
                        </Badge>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold">
                        {(strategy.accuracy * 100).toFixed(1)}%
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {strategy.correct}/{strategy.total}
                      </p>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <Progress value={strategy.accuracy * 100} className="h-2" />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Coverage: {(strategy.coverage * 100).toFixed(1)}%</span>
                      <span>{strategy.total} fields</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Insights */}
        <div className="p-4 rounded-lg bg-muted/50 space-y-2">
          <h4 className="text-sm font-semibold flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Key Insights
          </h4>
          <ul className="text-sm space-y-1 text-muted-foreground">
            {data.improvement_over_best > 5 && (
              <li>✅ Hybrid approach significantly outperforms single strategies (+{data.improvement_over_best.toFixed(1)}%)</li>
            )}
            {data.improvement_over_best > 0 && data.improvement_over_best <= 5 && (
              <li>✅ Hybrid approach provides modest improvement (+{data.improvement_over_best.toFixed(1)}%)</li>
            )}
            {data.improvement_over_best < 0 && (
              <li>⚠️ Single strategy ({data.best_single_strategy}) performs better - consider tuning hybrid weights</li>
            )}
            {data.improvement_over_best === 0 && (
              <li>ℹ️ Hybrid and best single strategy have equal performance</li>
            )}
            <li>
              📊 Tested {data.strategies.length} strategies across {data.hybrid_total} field extractions
            </li>
            <li>
              🎯 Best single strategy: {data.best_single_strategy?.replace('_', ' ')} ({(data.best_single_accuracy * 100).toFixed(1)}%)
            </li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
