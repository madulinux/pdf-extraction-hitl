import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Brain, Zap, CheckCircle2, XCircle, Clock } from "lucide-react";
import { Progress } from "@/components/ui/progress";

interface AdaptiveLearningStatus {
  pattern_learning: {
    total_patterns: number;
    active_patterns: number;
    patterns_by_type: Record<string, number>;
    pattern_effectiveness: Record<string, number>;
    avg_pattern_usage: number;
  };
  auto_training: {
    total_jobs: number;
    completed_jobs: number;
    failed_jobs: number;
    training_frequency: string;
    last_training: string | null;
    patterns_discovered_total: number;
  };
  recent_jobs: Array<{
    field_name: string;
    status: string;
    patterns_discovered: number;
    patterns_applied: number;
    completed_at: string;
  }>;
}

interface AdaptiveLearningStatusCardProps {
  data: AdaptiveLearningStatus;
}

export function AdaptiveLearningStatusCard({ data }: AdaptiveLearningStatusCardProps) {
  const successRate = data.auto_training.total_jobs > 0
    ? (data.auto_training.completed_jobs / data.auto_training.total_jobs) * 100
    : 0;

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* Pattern Learning Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Pattern Learning
          </CardTitle>
          <CardDescription>
            Automatically discovered extraction patterns
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-2xl font-bold">{data.pattern_learning.total_patterns}</p>
              <p className="text-xs text-muted-foreground">Total patterns learned</p>
            </div>
            <Badge variant={data.pattern_learning.active_patterns > 0 ? "default" : "secondary"}>
              {data.pattern_learning.active_patterns} Active
            </Badge>
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium">Pattern Types:</p>
            {Object.entries(data.pattern_learning.patterns_by_type).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground capitalize">
                  {type.replace(/_/g, ' ')}
                </span>
                <span className="font-medium">{count}</span>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Avg usage per pattern:</span>
              <span className="font-medium">{data.pattern_learning.avg_pattern_usage.toFixed(1)}</span>
            </div>
          </div>

          {Object.keys(data.pattern_learning.pattern_effectiveness).length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium">Pattern Effectiveness:</p>
              {Object.entries(data.pattern_learning.pattern_effectiveness)
                .slice(0, 3)
                .map(([field, effectiveness]) => (
                  <div key={field} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="truncate">{field}</span>
                      <span className="font-medium">{(effectiveness * 100).toFixed(0)}%</span>
                    </div>
                    <Progress value={effectiveness * 100} className="h-1" />
                  </div>
                ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Auto-Training Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Auto-Training
          </CardTitle>
          <CardDescription>
            Automatic model training and updates
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-2xl font-bold">{data.auto_training.total_jobs}</p>
              <p className="text-xs text-muted-foreground">Total jobs</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-600">
                {data.auto_training.completed_jobs}
              </p>
              <p className="text-xs text-muted-foreground">Completed</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-red-600">
                {data.auto_training.failed_jobs}
              </p>
              <p className="text-xs text-muted-foreground">Failed</p>
            </div>
          </div>

          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Success Rate:</span>
              <Badge variant={successRate > 80 ? "default" : "secondary"}>
                {successRate.toFixed(0)}%
              </Badge>
            </div>
            <Progress value={successRate} className="h-2" />
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Training frequency:</span>
              <span className="font-medium">{data.auto_training.training_frequency}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Patterns discovered:</span>
              <span className="font-medium">{data.auto_training.patterns_discovered_total}</span>
            </div>
            {data.auto_training.last_training && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Last training:</span>
                <span className="font-medium text-xs">
                  {new Date(data.auto_training.last_training).toLocaleDateString()}
                </span>
              </div>
            )}
          </div>

          {data.recent_jobs.length > 0 && (
            <div className="space-y-2 pt-2 border-t">
              <p className="text-sm font-medium">Recent Jobs:</p>
              {data.recent_jobs.slice(0, 3).map((job, idx) => (
                <div key={idx} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    {job.status === "completed" ? (
                      <CheckCircle2 className="h-3 w-3 text-green-600" />
                    ) : job.status === "failed" ? (
                      <XCircle className="h-3 w-3 text-red-600" />
                    ) : (
                      <Clock className="h-3 w-3 text-yellow-600" />
                    )}
                    <span className="truncate max-w-[120px]">{job.field_name}</span>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {job.patterns_applied || 0} patterns
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
