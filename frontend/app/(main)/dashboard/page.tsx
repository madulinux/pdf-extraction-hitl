"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  TrendingUp,
  FileText,
  CheckCircle2,
  AlertCircle,
  Activity,
  RefreshCw,
} from "lucide-react";
import { PerformanceMetrics } from "./components/PerformanceMetrics";
import { AccuracyChart } from "./components/AccuracyChart";
import { FieldPerformanceTable } from "./components/FieldPerformanceTable";
import { StrategyDistribution } from "./components/StrategyDistribution";
import { RecentFeedback } from "./components/RecentFeedback";
import { LearningProgressChart } from "./components/LearningProgressChart"; // ✅ NEW
import { StrategyPerformanceTable } from "./components/StrategyPerformanceTable"; // ✅ NEW
import { ErrorPatternsCard } from "./components/ErrorPatternsCard"; // ✅ NEW
import { ConfidenceTrendsCard } from "./components/ConfidenceTrendsCard"; // ✅ NEW
import { StrategyLearningComparison } from "./components/StrategyLearningComparison"; // ✅ NEW
import { FieldMetricsDetailedTable } from "./components/FieldMetricsDetailedTable"; // ✅ NEW
import { ExtractionTimeStats } from "./components/ExtractionTimeStats"; // ✅ NEW
import { AblationStudyCard } from "./components/AblationStudyCard"; // ✅ NEW
import { TimeTrendsChart } from "./components/TimeTrendsChart"; // ✅ NEW
// ✅ PHASE 1: Critical metrics for thesis
import { HitlMetricsCard } from "./components/HitlMetricsCard"; // ✅ PHASE 1
import { AdaptiveLearningStatusCard } from "./components/AdaptiveLearningStatusCard"; // ✅ PHASE 1
import { IncrementalLearningChart } from "./components/IncrementalLearningChart"; // ✅ PHASE 1
import { BaselineComparisonCard } from "./components/BaselineComparisonCard"; // ✅ PHASE 1
import { getPerformanceMetrics } from "@/lib/api/learning.api";
import { toast } from "sonner";
import type { PerformanceMetrics as PerformanceMetricsType } from "@/lib/types/dashboard.types";
import { templatesAPI } from "@/lib/api";
import { Template } from "@/lib/types/template.types";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const phases = [
  { value: "adaptive", label: "Adaptive" },
  { value: "baseline", label: "Baseline" },
];

export default function DashboardPage() {
  const [phase, setPhase] = useState<string>("adaptive");
  const [metrics, setMetrics] = useState<PerformanceMetricsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(
    null
  );
  const [selectedTab, setSelectedTab] = useState<string>("overview");

  useEffect(() => {
    fetchTemplates();
  }, []);

  const loadMetrics = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getPerformanceMetrics(
        selectedTemplate?.id || 1,
        phase
      );
      console.log("Metrics data received:", data);
      setMetrics(data);
    } catch (error) {
      console.error("Failed to load metrics:", error);
      toast.error("Failed to load performance metrics");
    } finally {
      setLoading(false);
    }
  }, [selectedTemplate, phase]);

  useEffect(() => {
    loadMetrics();
  }, [selectedTemplate, loadMetrics, phase]);

  const fetchTemplates = useCallback(async () => {
    try {
      const data = await templatesAPI.list();
      const res = data.templates.map((template) => ({
        ...template,
      })) as Template[];
      setTemplates(res);
    } catch (error) {
      console.error("Failed to load templates:", error);
      toast.error("Failed to load templates");
    }
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center gap-4">
          <RefreshCw className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">
            Loading performance metrics...
          </p>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">No Data Available</h2>
          <p className="text-muted-foreground mb-4">
            No performance data found for this template
          </p>
          <Button onClick={loadMetrics}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const {
    overview,
    field_performance,
    field_metrics_detailed, // ✅ NEW: Precision, Recall, F1
    strategy_distribution,
    strategy_performance, // ✅ NEW
    accuracy_over_time,
    feedback_stats,
    learning_progress, // ✅ NEW
    confidence_trends, // ✅ NEW
    error_patterns, // ✅ NEW
    performance_stats, // ✅ NEW: Extraction time
    ablation_study, // ✅ NEW: Strategy comparison
    time_trends, // ✅ NEW: Time trends
    // ✅ PHASE 1: Critical metrics for thesis
    hitl_metrics,
    adaptive_learning_status,
    incremental_learning,
    baseline_comparison,
  } = metrics;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Performance Dashboard
          </h1>
          <p className="text-muted-foreground mt-1">
            Monitor adaptive learning and extraction performance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select
            value={selectedTemplate?.id?.toString() || ""}
            onValueChange={(value) => {
              const t = templates.find(
                (template) => template.id.toString() === value
              );
              if (t) {
                setSelectedTemplate(t);
              }
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select a template" />
            </SelectTrigger>
            <SelectContent>
              {templates.map((template) => (
                <SelectItem key={template.id} value={template.id.toString()}>
                  {template.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={phase} onValueChange={setPhase}>
            <SelectTrigger>
              <SelectValue placeholder="Select a phase" />
            </SelectTrigger>
            <SelectContent>
              {phases.map((phase) => (
                <SelectItem key={phase.value} value={phase.value}>
                  {phase.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={loadMetrics} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Documents
            </CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview.total_documents}</div>
            <p className="text-xs text-muted-foreground">
              {overview.validated_documents} validated
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Overall Accuracy
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(overview.overall_accuracy * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              {overview.total_corrections} corrections made
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Validation Rate
            </CardTitle>
            <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(overview.validation_rate * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              Documents validated by users
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Feedback
            </CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {feedback_stats.total_feedback}
            </div>
            <p className="text-xs text-muted-foreground">
              User corrections collected
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue={selectedTab} className="space-y-4">
        <TabsList>
          <TabsTrigger
            value="overview"
            onClick={() => setSelectedTab("overview")}
          >
            Overview
          </TabsTrigger>
          <TabsTrigger
            value="learning"
            onClick={() => setSelectedTab("learning")}
          >
            Learning Progress
          </TabsTrigger>
          <TabsTrigger value="fields" onClick={() => setSelectedTab("fields")}>
            Field Performance
          </TabsTrigger>
          <TabsTrigger
            value="evaluation"
            onClick={() => setSelectedTab("evaluation")}
          >
            Evaluation Metrics
          </TabsTrigger>
          <TabsTrigger
            value="performance"
            onClick={() => setSelectedTab("performance")}
          >
            Performance
          </TabsTrigger>
          <TabsTrigger
            value="strategies"
            onClick={() => setSelectedTab("strategies")}
          >
            Strategies
          </TabsTrigger>
          <TabsTrigger value="errors" onClick={() => setSelectedTab("errors")}>
            Error Patterns
          </TabsTrigger>
          <TabsTrigger
            value="feedback"
            onClick={() => setSelectedTab("feedback")}
          >
            Feedback
          </TabsTrigger>
          <TabsTrigger
            value="research"
            onClick={() => setSelectedTab("research")}
          >
            Research Metrics
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Accuracy Over Time</CardTitle>
              <CardDescription>
                Track how extraction accuracy improves with adaptive learning
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AccuracyChart data={accuracy_over_time} />
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Strategy Distribution</CardTitle>
                <CardDescription>
                  Which extraction strategies are being used
                </CardDescription>
              </CardHeader>
              <CardContent>
                <StrategyDistribution data={strategy_distribution} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
                <CardDescription>Key performance indicators</CardDescription>
              </CardHeader>
              <CardContent>
                <PerformanceMetrics overview={overview} />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Learning Progress Tab - NEW */}
        <TabsContent value="learning" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Adaptive Learning Progress</CardTitle>
              <CardDescription>
                Track how the model improves over time with feedback
              </CardDescription>
            </CardHeader>
            <CardContent>
              <LearningProgressChart data={learning_progress} />
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Confidence Trends</CardTitle>
                <CardDescription>
                  Model confidence scores by strategy
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ConfidenceTrendsCard data={confidence_trends} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Key Insights</CardTitle>
                <CardDescription>Performance highlights</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                    <span className="text-sm font-medium">
                      Improvement Rate
                    </span>
                    <Badge variant="default" className="text-base">
                      +{learning_progress.improvement_rate.toFixed(1)}%
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                    <span className="text-sm font-medium">Total Batches</span>
                    <span className="text-lg font-bold">
                      {learning_progress.total_batches}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                    <span className="text-sm font-medium">Avg Confidence</span>
                    <span className="text-lg font-bold">
                      {(confidence_trends.avg_confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Strategy Learning Comparison - NEW */}
          <Card>
            <CardHeader>
              <CardTitle>Strategy Performance Comparison</CardTitle>
              <CardDescription>
                Compare learning effectiveness across extraction strategies
              </CardDescription>
            </CardHeader>
            <CardContent>
              <StrategyLearningComparison
                strategyPerformance={strategy_performance}
                accuracyOverTime={accuracy_over_time}
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Field Performance Tab */}
        <TabsContent value="fields" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Field-Level Performance</CardTitle>
              <CardDescription>
                Detailed accuracy metrics for each field
              </CardDescription>
            </CardHeader>
            <CardContent>
              <FieldPerformanceTable data={field_performance} />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Evaluation Metrics Tab - NEW */}
        <TabsContent value="evaluation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Detailed Evaluation Metrics</CardTitle>
              <CardDescription>
                Precision, Recall, and F1-Score for each field (for thesis
                documentation)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <FieldMetricsDetailedTable data={field_metrics_detailed} />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Performance Tab - NEW */}
        <TabsContent value="performance" className="space-y-4">
          <ExtractionTimeStats stats={performance_stats} />

          <TimeTrendsChart data={time_trends} />

          <AblationStudyCard data={ablation_study} />
        </TabsContent>

        {/* Strategies Tab */}
        <TabsContent value="strategies" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Strategy Distribution</CardTitle>
                <CardDescription>
                  Which strategies are selected most often
                </CardDescription>
              </CardHeader>
              <CardContent>
                <StrategyDistribution data={strategy_distribution} detailed />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Strategy Performance</CardTitle>
                <CardDescription>
                  Accuracy and effectiveness of each strategy
                </CardDescription>
              </CardHeader>
              <CardContent>
                <StrategyPerformanceTable data={strategy_performance} />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Error Patterns Tab - NEW */}
        <TabsContent value="errors" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Error Pattern Analysis</CardTitle>
              <CardDescription>
                Identify problematic fields and common mistakes
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ErrorPatternsCard data={error_patterns} />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Feedback Tab */}
        <TabsContent value="feedback" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Feedback</CardTitle>
              <CardDescription>
                Latest user corrections and improvements
              </CardDescription>
            </CardHeader>
            <CardContent>
              <RecentFeedback data={feedback_stats.recent_feedback} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Feedback by Field</CardTitle>
              <CardDescription>
                Which fields receive the most corrections
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {Object.entries(feedback_stats.feedback_by_field)
                  .sort(([, a], [, b]) => b - a)
                  .map(([field, count]) => (
                    <div
                      key={field}
                      className="flex items-center justify-between"
                    >
                      <span className="text-sm font-medium capitalize">
                        {field.replace(/_/g, " ")}
                      </span>
                      <Badge variant="secondary">{count} corrections</Badge>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Research Metrics Tab - PHASE 1 */}
        <TabsContent value="research" className="space-y-4">
          {/* Human-in-the-Loop Metrics */}
          <div>
            <h2 className="text-2xl font-bold mb-4">
              Human-in-the-Loop Metrics
            </h2>
            <HitlMetricsCard data={hitl_metrics} />
          </div>

          {/* Adaptive Learning Status */}
          <div>
            <h2 className="text-2xl font-bold mb-4">
              Adaptive Learning Status
            </h2>
            <AdaptiveLearningStatusCard data={adaptive_learning_status} />
          </div>

          {/* Incremental Learning Progress */}
          <div>
            <h2 className="text-2xl font-bold mb-4">
              Incremental Learning Progress
            </h2>
            <IncrementalLearningChart data={incremental_learning} />
          </div>

          {/* Baseline Comparison */}
          <div>
            <h2 className="text-2xl font-bold mb-4">Baseline Comparison</h2>
            <BaselineComparisonCard data={baseline_comparison} />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
