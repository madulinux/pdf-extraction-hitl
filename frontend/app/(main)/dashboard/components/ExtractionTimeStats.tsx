"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Clock, Zap, TrendingDown, TrendingUp } from "lucide-react";
import type { PerformanceStats } from "@/lib/types/dashboard.types";

interface ExtractionTimeStatsProps {
  stats: PerformanceStats;
}

export function ExtractionTimeStats({ stats }: ExtractionTimeStatsProps) {
  if (!stats || stats.documents_timed === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Extraction Time Statistics
          </CardTitle>
          <CardDescription>
            Performance metrics for document extraction
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <Clock className="h-12 w-12 mb-4 opacity-50" />
            <p className="text-sm">⚠️ No extraction time data available (old documents)</p>
            <p className="text-xs mt-2">Extraction time tracking was just added.</p>
            <p className="text-xs">New extractions will include timing data.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const getPerformanceLevel = (avgTime: number) => {
    if (avgTime < 50) return { label: "Excellent", color: "bg-green-500", icon: Zap };
    if (avgTime < 100) return { label: "Good", color: "bg-blue-500", icon: TrendingDown };
    if (avgTime < 200) return { label: "Fair", color: "bg-yellow-500", icon: TrendingUp };
    return { label: "Slow", color: "bg-red-500", icon: Clock };
  };

  const performance = getPerformanceLevel(stats.avg_time_ms);
  const PerformanceIcon = performance.icon;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Extraction Time Statistics
        </CardTitle>
        <CardDescription>
          Performance metrics for {stats.documents_timed} documents
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Overall Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">Average Time</p>
            <div className="flex items-center gap-2">
              <p className="text-2xl font-bold">{stats.avg_time_ms.toFixed(1)}</p>
              <span className="text-xs text-muted-foreground">ms</span>
            </div>
            <Badge className={performance.color}>
              <PerformanceIcon className="h-3 w-3 mr-1" />
              {performance.label}
            </Badge>
          </div>

          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">Min Time</p>
            <div className="flex items-center gap-2">
              <p className="text-2xl font-bold text-green-600">{stats.min_time_ms}</p>
              <span className="text-xs text-muted-foreground">ms</span>
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">Max Time</p>
            <div className="flex items-center gap-2">
              <p className="text-2xl font-bold text-red-600">{stats.max_time_ms}</p>
              <span className="text-xs text-muted-foreground">ms</span>
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">Total Time</p>
            <div className="flex items-center gap-2">
              <p className="text-2xl font-bold">{stats.total_time_sec.toFixed(2)}</p>
              <span className="text-xs text-muted-foreground">sec</span>
            </div>
          </div>
        </div>

        {/* Strategy Breakdown */}
        {Object.keys(stats.by_strategy).length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-semibold">Performance by Strategy</h4>
            <div className="space-y-2">
              {Object.entries(stats.by_strategy)
                .sort(([, a], [, b]) => a.avg_time_ms - b.avg_time_ms)
                .map(([strategy, strategyStats]) => {
                  const strategyPerf = getPerformanceLevel(strategyStats.avg_time_ms);
                  return (
                    <div
                      key={strategy}
                      className="flex items-center justify-between p-3 rounded-lg border bg-card"
                    >
                      <div className="flex items-center gap-3">
                        <Badge variant="outline" className="capitalize">
                          {strategy.replace('_', ' ')}
                        </Badge>
                        <div className="text-sm">
                          <span className="font-medium">{strategyStats.avg_time_ms.toFixed(1)} ms</span>
                          <span className="text-muted-foreground ml-2">
                            ({strategyStats.count} docs)
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">
                          {strategyStats.min_time_ms}-{strategyStats.max_time_ms} ms
                        </span>
                        <Badge className={strategyPerf.color} variant="secondary">
                          {strategyPerf.label}
                        </Badge>
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        )}

        {/* Performance Insights */}
        <div className="p-4 rounded-lg bg-muted/50 space-y-2">
          <h4 className="text-sm font-semibold flex items-center gap-2">
            <Zap className="h-4 w-4" />
            Performance Insights
          </h4>
          <ul className="text-sm space-y-1 text-muted-foreground">
            {stats.avg_time_ms < 50 && (
              <li>✅ Excellent performance - extraction is very fast</li>
            )}
            {stats.avg_time_ms >= 50 && stats.avg_time_ms < 100 && (
              <li>✅ Good performance - extraction speed is acceptable</li>
            )}
            {stats.avg_time_ms >= 100 && (
              <li>⚠️ Consider optimization - extraction could be faster</li>
            )}
            <li>
              📊 Processed {stats.documents_timed} documents in {stats.total_time_sec.toFixed(2)}s
            </li>
            <li>
              ⚡ Throughput: ~{(stats.documents_timed / stats.total_time_sec).toFixed(1)} docs/sec
            </li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
