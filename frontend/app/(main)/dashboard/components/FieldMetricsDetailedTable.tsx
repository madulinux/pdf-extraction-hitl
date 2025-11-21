"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import type { FieldMetricsDetailed } from "@/lib/types/dashboard.types";
import { Info } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface FieldMetricsDetailedTableProps {
  data: Record<string, FieldMetricsDetailed>;
}

export function FieldMetricsDetailedTable({ data }: FieldMetricsDetailedTableProps) {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        No detailed metrics available
      </div>
    );
  }

  // Sort by F1-Score (descending)
  const sortedFields = Object.entries(data).sort(
    ([, a], [, b]) => b.f1_score - a.f1_score
  );

  const getScoreColor = (score: number) => {
    if (score >= 0.9) return "text-green-600";
    if (score >= 0.7) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreBadge = (score: number) => {
    if (score >= 0.9) return "default";
    if (score >= 0.7) return "secondary";
    return "destructive";
  };

  return (
    <div className="space-y-4">
      {/* Info Banner */}
      <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5" />
          <div className="space-y-1 text-sm">
            <p className="font-semibold text-blue-900 dark:text-blue-100">
              Evaluation Metrics Explained:
            </p>
            <ul className="space-y-1 text-blue-700 dark:text-blue-300">
              <li>
                <span className="font-medium">Precision:</span> Of all extracted values, how many are correct? (TP / (TP + FP))
              </li>
              <li>
                <span className="font-medium">Recall:</span> Of all values that should be extracted, how many are? (TP / (TP + FN))
              </li>
              <li>
                <span className="font-medium">F1-Score:</span> Harmonic mean of Precision and Recall (2 × P × R / (P + R))
              </li>
              <li>
                <span className="font-medium">Support:</span> Total number of instances for this field
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Field Name</TableHead>
              <TableHead>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger className="flex items-center gap-1">
                      Precision
                      <Info className="h-3 w-3" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Accuracy of positive predictions</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </TableHead>
              <TableHead>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger className="flex items-center gap-1">
                      Recall
                      <Info className="h-3 w-3" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Coverage of actual positives</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </TableHead>
              <TableHead>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger className="flex items-center gap-1">
                      F1-Score
                      <Info className="h-3 w-3" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Balanced measure (harmonic mean)</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </TableHead>
              <TableHead className="text-center">TP</TableHead>
              <TableHead className="text-center">FP</TableHead>
              <TableHead className="text-center">FN</TableHead>
              <TableHead className="text-center">Support</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedFields.map(([fieldName, metrics]) => (
              <TableRow key={fieldName}>
                <TableCell className="font-medium capitalize">
                  {fieldName.replace(/_/g, " ")}
                </TableCell>
                
                {/* Precision */}
                <TableCell>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`font-bold ${getScoreColor(metrics.precision)}`}>
                        {(metrics.precision * 100).toFixed(1)}%
                      </span>
                    </div>
                    <Progress value={metrics.precision * 100} className="h-1" />
                  </div>
                </TableCell>
                
                {/* Recall */}
                <TableCell>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`font-bold ${getScoreColor(metrics.recall)}`}>
                        {(metrics.recall * 100).toFixed(1)}%
                      </span>
                    </div>
                    <Progress value={metrics.recall * 100} className="h-1" />
                  </div>
                </TableCell>
                
                {/* F1-Score */}
                <TableCell>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`font-bold ${getScoreColor(metrics.f1_score)}`}>
                        {(metrics.f1_score * 100).toFixed(1)}%
                      </span>
                      <Badge variant={getScoreBadge(metrics.f1_score)} className="text-xs">
                        {metrics.f1_score >= 0.9 ? "Excellent" : metrics.f1_score >= 0.7 ? "Good" : "Needs Work"}
                      </Badge>
                    </div>
                    <Progress value={metrics.f1_score * 100} className="h-1" />
                  </div>
                </TableCell>
                
                {/* TP */}
                <TableCell className="text-center">
                  <Badge variant="default" className="bg-green-500">
                    {metrics.tp}
                  </Badge>
                </TableCell>
                
                {/* FP */}
                <TableCell className="text-center">
                  <Badge variant="destructive">
                    {metrics.fp}
                  </Badge>
                </TableCell>
                
                {/* FN */}
                <TableCell className="text-center">
                  <Badge variant="secondary">
                    {metrics.fn}
                  </Badge>
                </TableCell>
                
                {/* Support */}
                <TableCell className="text-center">
                  <Badge variant="outline">
                    {metrics.support}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-muted/50 rounded-lg p-4">
          <p className="text-sm text-muted-foreground mb-1">Avg Precision</p>
          <p className="text-2xl font-bold">
            {(
              (Object.values(data).reduce((sum, m) => sum + m.precision, 0) /
                Object.values(data).length) *
              100
            ).toFixed(1)}
            %
          </p>
        </div>
        <div className="bg-muted/50 rounded-lg p-4">
          <p className="text-sm text-muted-foreground mb-1">Avg Recall</p>
          <p className="text-2xl font-bold">
            {(
              (Object.values(data).reduce((sum, m) => sum + m.recall, 0) /
                Object.values(data).length) *
              100
            ).toFixed(1)}
            %
          </p>
        </div>
        <div className="bg-muted/50 rounded-lg p-4">
          <p className="text-sm text-muted-foreground mb-1">Avg F1-Score</p>
          <p className="text-2xl font-bold">
            {(
              (Object.values(data).reduce((sum, m) => sum + m.f1_score, 0) /
                Object.values(data).length) *
              100
            ).toFixed(1)}
            %
          </p>
        </div>
      </div>
    </div>
  );
}
