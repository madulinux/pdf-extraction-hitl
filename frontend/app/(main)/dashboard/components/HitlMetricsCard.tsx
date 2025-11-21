import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Users, TrendingUp, Target } from "lucide-react";

interface HitlMetrics {
  feedback_quality: {
    avg_feedback_per_document: number;
    total_feedback: number;
    documents_with_feedback: number;
    quality_score: number;
  };
  human_effort: {
    total_corrections: number;
    avg_corrections_per_document: number;
    corrections_by_field: Record<string, number>;
  };
  learning_efficiency: {
    feedback_to_improvement_ratio: number;
    total_batches: number;
    avg_improvement_per_batch: number;
  };
}

interface HitlMetricsCardProps {
  data: HitlMetrics;
}

export function HitlMetricsCard({ data }: HitlMetricsCardProps) {
  const qualityPercentage = data.feedback_quality.quality_score * 100;
  const topFields = Object.entries(data.human_effort.corrections_by_field)
    .slice(0, 5);

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {/* Feedback Quality */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Feedback Quality</CardTitle>
          <Target className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-2xl font-bold">
                  {qualityPercentage.toFixed(0)}%
                </span>
                <Badge variant={qualityPercentage > 70 ? "default" : "secondary"}>
                  {qualityPercentage > 70 ? "High" : "Medium"}
                </Badge>
              </div>
              <Progress value={qualityPercentage} className="h-2" />
            </div>
            
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Avg per doc:</span>
                <span className="font-medium">
                  {data.feedback_quality.avg_feedback_per_document.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total feedback:</span>
                <span className="font-medium">
                  {data.feedback_quality.total_feedback}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Docs with feedback:</span>
                <span className="font-medium">
                  {data.feedback_quality.documents_with_feedback}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Human Effort */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Human Effort</CardTitle>
          <Users className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div>
              <div className="text-2xl font-bold">
                {data.human_effort.total_corrections}
              </div>
              <p className="text-xs text-muted-foreground">
                Total corrections made
              </p>
            </div>
            
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground">
                Most corrected fields:
              </p>
              {topFields.map(([field, count]) => (
                <div key={field} className="flex items-center justify-between text-sm">
                  <span className="truncate flex-1 mr-2">{field}</span>
                  <Badge variant="outline" className="text-xs">
                    {count}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Learning Efficiency */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Learning Efficiency</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div>
              <div className="text-2xl font-bold">
                {(data.learning_efficiency.feedback_to_improvement_ratio * 100).toFixed(2)}%
              </div>
              <p className="text-xs text-muted-foreground">
                Improvement per feedback
              </p>
            </div>
            
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total batches:</span>
                <span className="font-medium">
                  {data.learning_efficiency.total_batches}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Avg improvement:</span>
                <span className="font-medium">
                  {(data.learning_efficiency.avg_improvement_per_batch * 100).toFixed(2)}%
                </span>
              </div>
            </div>
            
            <div className="pt-2 border-t">
              <p className="text-xs text-muted-foreground">
                {data.learning_efficiency.feedback_to_improvement_ratio > 0.01
                  ? "✅ Efficient learning from feedback"
                  : "⚠️ More feedback needed for improvement"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
