import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from "recharts";
import { Trophy, TrendingUp, Zap } from "lucide-react";

interface SystemMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  total_extractions: number;
  correct_extractions: number;
  avg_time_ms: number;
}

interface BaselineComparison {
  systems: Record<string, SystemMetrics>;
  comparison: {
    best_strategy: string;
    worst_strategy: string;
  };
  improvement: {
    hybrid_over_rule: number;
    hybrid_over_crf: number;
    hybrid_accuracy: number;
  };
}

interface BaselineComparisonCardProps {
  data: BaselineComparison;
}

const COLORS = {
  rule_based: "#3b82f6",
  crf: "#8b5cf6",
  hybrid: "#22c55e",
  position_based: "#f59e0b"
};

export function BaselineComparisonCard({ data }: BaselineComparisonCardProps) {
  // Prepare chart data
  const chartData = Object.entries(data.systems).map(([name, metrics]) => ({
    name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    accuracy: (metrics.accuracy * 100).toFixed(2),
    precision: (metrics.precision * 100).toFixed(2),
    recall: (metrics.recall * 100).toFixed(2),
    f1: (metrics.f1_score * 100).toFixed(2),
    time: metrics.avg_time_ms,
    total: metrics.total_extractions,
    correct: metrics.correct_extractions,
    originalName: name
  }));

  const bestSystem = data.systems[data.comparison.best_strategy];
  const hybridSystem = data.systems.hybrid;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5" />
              Baseline Comparison
            </CardTitle>
            <CardDescription>
              Hybrid Adaptive vs Traditional Approaches
            </CardDescription>
          </div>
          <Badge variant="default" className="text-sm">
            Best: {data.comparison.best_strategy.replace(/_/g, ' ')}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Key Improvements */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-green-50 dark:bg-green-950 rounded-lg">
              <div className="flex items-center justify-center gap-1 mb-1">
                <TrendingUp className="h-4 w-4 text-green-600" />
                <p className="text-xs font-medium text-green-600">vs Rule-Based</p>
              </div>
              <p className={`text-2xl font-bold ${data.improvement.hybrid_over_rule >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {data.improvement.hybrid_over_rule >= 0 ? '+' : ''}{data.improvement.hybrid_over_rule.toFixed(1)}%
              </p>
            </div>
            <div className="text-center p-4 bg-purple-50 dark:bg-purple-950 rounded-lg">
              <div className="flex items-center justify-center gap-1 mb-1">
                <TrendingUp className="h-4 w-4 text-purple-600" />
                <p className="text-xs font-medium text-purple-600">vs CRF Only</p>
              </div>
              <p className={`text-2xl font-bold ${data.improvement.hybrid_over_crf >= 0 ? 'text-purple-600' : 'text-orange-600'}`}>
                {data.improvement.hybrid_over_crf >= 0 ? '+' : ''}{data.improvement.hybrid_over_crf.toFixed(1)}%
              </p>
            </div>
            <div className="text-center p-4 bg-blue-50 dark:bg-blue-950 rounded-lg">
              <div className="flex items-center justify-center gap-1 mb-1">
                <Zap className="h-4 w-4 text-blue-600" />
                <p className="text-xs font-medium text-blue-600">Hybrid Accuracy</p>
              </div>
              <p className="text-2xl font-bold text-blue-600">
                {data.improvement.hybrid_accuracy.toFixed(1)}%
              </p>
            </div>
          </div>

          {/* Accuracy Comparison Chart */}
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  tick={{ fontSize: 11 }}
                  angle={-15}
                  textAnchor="end"
                  height={60}
                />
                <YAxis 
                  label={{ value: 'Accuracy (%)', angle: -90, position: 'insideLeft' }}
                  domain={[0, 100]}
                />
                <Tooltip 
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-background border rounded-lg p-3 shadow-lg">
                          <p className="font-semibold mb-2">{data.name}</p>
                          <div className="space-y-1 text-sm">
                            <p>Accuracy: <span className="font-semibold">{data.accuracy}%</span></p>
                            <p>Precision: <span className="font-semibold">{data.precision}%</span></p>
                            <p>Recall: <span className="font-semibold">{data.recall}%</span></p>
                            <p>F1-Score: <span className="font-semibold">{data.f1}%</span></p>
                            <p className="text-muted-foreground pt-1 border-t">
                              {data.correct}/{data.total} correct
                            </p>
                            <p className="text-muted-foreground">
                              Avg time: {data.time.toFixed(0)}ms
                            </p>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend />
                <Bar dataKey="accuracy" name="Accuracy (%)" radius={[8, 8, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={COLORS[entry.originalName as keyof typeof COLORS] || "#94a3b8"} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Detailed Metrics Table */}
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="text-left p-2 font-medium">Strategy</th>
                  <th className="text-center p-2 font-medium">Accuracy</th>
                  <th className="text-center p-2 font-medium">Precision</th>
                  <th className="text-center p-2 font-medium">Recall</th>
                  <th className="text-center p-2 font-medium">F1-Score</th>
                  <th className="text-center p-2 font-medium">Time (ms)</th>
                </tr>
              </thead>
              <tbody>
                {chartData.map((row, idx) => (
                  <tr 
                    key={idx} 
                    className={`border-t ${row.originalName === 'hybrid' ? 'bg-green-50 dark:bg-green-950' : ''}`}
                  >
                    <td className="p-2 font-medium">
                      <div className="flex items-center gap-2">
                        {row.name}
                        {row.originalName === data.comparison.best_strategy && (
                          <Trophy className="h-3 w-3 text-yellow-600" />
                        )}
                      </div>
                    </td>
                    <td className="text-center p-2">{row.accuracy}%</td>
                    <td className="text-center p-2">{row.precision}%</td>
                    <td className="text-center p-2">{row.recall}%</td>
                    <td className="text-center p-2">{row.f1}%</td>
                    <td className="text-center p-2">{row.time.toFixed(0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Insights */}
          <div className="bg-muted p-4 rounded-lg">
            <p className="text-sm font-medium mb-2">Key Insights:</p>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>
                • Hybrid adaptive approach achieves <strong>{data.improvement.hybrid_accuracy.toFixed(1)}%</strong> accuracy
              </li>
              <li>
                • <strong>{data.improvement.hybrid_over_rule > 0 ? 'Outperforms' : 'Comparable to'}</strong> rule-based by {Math.abs(data.improvement.hybrid_over_rule).toFixed(1)}%
              </li>
              <li>
                • <strong>{data.improvement.hybrid_over_crf > 0 ? 'Outperforms' : 'Comparable to'}</strong> CRF-only by {Math.abs(data.improvement.hybrid_over_crf).toFixed(1)}%
              </li>
              {hybridSystem && (
                <li>
                  • Processes {hybridSystem.total_extractions} extractions with {hybridSystem.avg_time_ms.toFixed(0)}ms avg time
                </li>
              )}
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
