"use client";

import { useEffect, useState, useCallback } from "react";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import {
  dashboardAPI,
  SystemOverview,
  LearningCurve,
  BaselineComparison,
} from "@/lib/api/dashboard.api";
import { SystemStatsCard } from "./components/SystemStatsCard";
import { TemplateCard } from "./components/TemplateCard";
import { HITLMetricsCard } from "./components/HITLMetricsCard";
import { LearningCurvesChart } from "./components/LearningCurvesChart";
import { BaselineComparisonTable } from "./components/BaselineComparisonTable";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  FileText,
  MessageSquare,
  TrendingUp,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import { toast } from "sonner";

const phases = [
  { value: "adaptive", label: "Adaptive" },
  { value: "baseline", label: "Baseline" },
  { value: "all", label: "All Data" },
];

function HomeContent() {
  const [phase, setPhase] = useState<string>("adaptive");
  const [overview, setOverview] = useState<SystemOverview | null>(null);
  const [learningCurves, setLearningCurves] = useState<LearningCurve[]>([]);
  const [baselineComparison, setBaselineComparison] = useState<{
    comparison: BaselineComparison[];
    summary: {
      documents: number;
      baseline_accuracy: number;
      adaptive_accuracy: number;
      improvement: number;
      batches: number;
    } | null;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  const loadOverview = useCallback(async () => {
    try {
      setLoading(true);
      const data = await dashboardAPI.getSystemOverview(phase);
      setOverview(data);

      // Load learning curves (only for adaptive phase)
      if (phase === "adaptive") {
        try {
          const curvesData = await dashboardAPI.getLearningCurves(phase);
          setLearningCurves(curvesData.learning_curves);
        } catch (error) {
          console.error("Failed to load learning curves:", error);
        }

        // Load baseline comparison
        try {
          const comparisonData = await dashboardAPI.getBaselineComparison();
          setBaselineComparison(comparisonData);
        } catch (error) {
          console.error("Failed to load baseline comparison:", error);
        }
      }
    } catch (error) {
      console.error("Failed to load overview:", error);
      toast.error("Failed to load system overview");
    } finally {
      setLoading(false);
    }
  }, [phase]);

  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center gap-4">
          <RefreshCw className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Loading system overview...</p>
        </div>
      </div>
    );
  }

  if (!overview) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">No Data Available</h2>
          <p className="text-muted-foreground mb-4">
            Unable to load system overview
          </p>
          <Button onClick={loadOverview}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const { system_stats, template_summaries, hitl_learning_metrics } = overview;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Overview</h1>
          <p className="text-muted-foreground mt-1">
            HITL-based adaptive learning system performance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={phase} onValueChange={setPhase}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select phase" />
            </SelectTrigger>
            <SelectContent>
              {phases.map((p) => (
                <SelectItem key={p.value} value={p.value}>
                  {p.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={loadOverview} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* System Stats - Enhanced with HITL metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <SystemStatsCard
          title="Total Documents"
          value={system_stats.total_documents}
          description={`${system_stats.total_validated} validated`}
          icon={FileText}
          tooltip="Total number of documents processed across all templates. All documents have been validated by users, ensuring data quality for the HITL learning system."
        />
        <SystemStatsCard
          title="Overall Accuracy"
          value={`${(system_stats.overall_accuracy * 100).toFixed(1)}%`}
          description="Field-level accuracy"
          icon={TrendingUp}
          tooltip="Field-level extraction accuracy calculated across all 2,800 fields (140 documents × 20 avg fields). This metric reflects the system's ability to correctly extract individual data fields from documents."
        />
        <SystemStatsCard
          title="Avg Feedback/Doc"
          value={system_stats.avg_feedback_per_doc.toFixed(2)}
          description="Minimal feedback needed"
          icon={MessageSquare}
          tooltip="Average number of user corrections required per document. Lower values indicate better initial extraction quality and reduced user burden, demonstrating the efficiency of the HITL learning approach."
        />
        <SystemStatsCard
          title="Learning Efficiency"
          value={`${(system_stats.learning_efficiency * 100).toFixed(2)}%`}
          description="Improvement per feedback"
          icon={TrendingUp}
          tooltip="Average accuracy improvement achieved per user feedback. This metric demonstrates how effectively the system learns from each correction, showing the incremental learning capability of the hybrid architecture."
        />
      </div>

      {/* HITL Learning Metrics */}
      <div className="grid gap-4">
        <HITLMetricsCard metrics={hitl_learning_metrics} />
      </div>

      {/* Template Cards */}
      <div>
        <h2 className="text-2xl font-bold mb-4">Templates</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {template_summaries.map((template) => (
            <TemplateCard key={template.id} template={template} />
          ))}
        </div>
      </div>

      {/* Thesis Visualizations - Only show for adaptive phase */}
      {phase === "adaptive" && learningCurves.length > 0 && (
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold mb-4">Thesis Visualizations</h2>
            <p className="text-muted-foreground mb-4">
              Comprehensive analysis for thesis documentation
            </p>
          </div>

          {/* Learning Curves */}
          <LearningCurvesChart learningCurves={learningCurves} />

          {/* Baseline vs Adaptive Comparison */}
          {baselineComparison && (
            <BaselineComparisonTable
              comparison={baselineComparison.comparison}
              summary={baselineComparison.summary}
            />
          )}
        </div>
      )}

      {/* Recent Activity */}
    </div>
  );
}

export default function Home() {
  return (
    <ProtectedRoute>
      <HomeContent />
    </ProtectedRoute>
  );
}
