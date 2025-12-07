"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { BaselineComparison } from "@/lib/api/dashboard.api";
import { Info, TrendingUp } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface BaselineComparisonTableProps {
  comparison: BaselineComparison[];
  summary: {
    documents: number;
    baseline_accuracy: number;
    adaptive_accuracy: number;
    improvement: number;
    batches: number;
  } | null;
}

const TEMPLATE_LABELS: Record<string, string> = {
  form_template: "Form",
  table_template: "Table",
  letter_template: "Letter",
  mixed_template: "Mixed",
};

export function BaselineComparisonTable({ comparison, summary }: BaselineComparisonTableProps) {
  const getImprovementColor = (improvement: number) => {
    if (improvement >= 30) return "text-green-600";
    if (improvement >= 20) return "text-yellow-600";
    return "text-orange-600";
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Baseline vs. Adaptive Comparison</CardTitle>
            <CardDescription>
              Performance improvement with HITL adaptive learning
            </CardDescription>
          </div>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="h-5 w-5 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent className="max-w-sm">
                <p className="font-semibold mb-2">Baseline vs Adaptive</p>
                <p className="text-sm">
                  Compares initial performance (baseline) with performance after
                  HITL adaptive learning. Shows the effectiveness of user feedback
                  in improving extraction accuracy.
                </p>
                <p className="text-sm mt-2">
                  <strong>Baseline:</strong> Initial extraction without feedback<br />
                  <strong>Adaptive:</strong> After incorporating user corrections
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[150px]">Template</TableHead>
                <TableHead className="text-center">Docs</TableHead>
                <TableHead className="text-center">Baseline</TableHead>
                <TableHead className="text-center">Adaptive</TableHead>
                <TableHead className="text-center">Improvement</TableHead>
                <TableHead className="text-center">Batches</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {comparison.map((item) => (
                <TableRow key={item.template_id}>
                  <TableCell className="font-medium">
                    {TEMPLATE_LABELS[item.template_name] || item.template_name}
                  </TableCell>
                  <TableCell className="text-center">{item.documents}</TableCell>
                  <TableCell className="text-center">
                    <span className="text-muted-foreground">
                      {item.baseline.accuracy.toFixed(2)}%
                    </span>
                  </TableCell>
                  <TableCell className="text-center">
                    <span className="font-semibold text-green-600">
                      {item.adaptive.accuracy.toFixed(2)}%
                    </span>
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge variant="outline" className={getImprovementColor(item.improvement)}>
                      <TrendingUp className="h-3 w-3 mr-1" />
                      +{item.improvement.toFixed(2)}%
                    </Badge>
                  </TableCell>
                  <TableCell className="text-center">{item.batches}</TableCell>
                </TableRow>
              ))}
              
              {/* Summary Row */}
              {summary && (
                <TableRow className="bg-muted/50 font-semibold">
                  <TableCell>Average</TableCell>
                  <TableCell className="text-center">{summary.documents}</TableCell>
                  <TableCell className="text-center">
                    {summary.baseline_accuracy.toFixed(2)}%
                  </TableCell>
                  <TableCell className="text-center text-green-600">
                    {summary.adaptive_accuracy.toFixed(2)}%
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge variant="default" className="bg-green-600">
                      <TrendingUp className="h-3 w-3 mr-1" />
                      +{summary.improvement.toFixed(2)}%
                    </Badge>
                  </TableCell>
                  <TableCell className="text-center">{summary.batches}</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        {/* Detailed Metrics Table */}
        <div className="mt-6">
          <h4 className="text-sm font-semibold mb-3">Detailed Metrics (Precision, Recall, F1)</h4>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead rowSpan={2} className="w-[120px]">Template</TableHead>
                  <TableHead colSpan={4} className="text-center border-r">Baseline</TableHead>
                  <TableHead colSpan={4} className="text-center">Adaptive</TableHead>
                </TableRow>
                <TableRow>
                  <TableHead className="text-center text-xs">Acc</TableHead>
                  <TableHead className="text-center text-xs">Prec</TableHead>
                  <TableHead className="text-center text-xs">Rec</TableHead>
                  <TableHead className="text-center text-xs border-r">F1</TableHead>
                  <TableHead className="text-center text-xs">Acc</TableHead>
                  <TableHead className="text-center text-xs">Prec</TableHead>
                  <TableHead className="text-center text-xs">Rec</TableHead>
                  <TableHead className="text-center text-xs">F1</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {comparison.map((item) => (
                  <TableRow key={item.template_id}>
                    <TableCell className="font-medium text-sm">
                      {TEMPLATE_LABELS[item.template_name] || item.template_name}
                    </TableCell>
                    {/* Baseline */}
                    <TableCell className="text-center text-sm">{item.baseline.accuracy.toFixed(2)}</TableCell>
                    <TableCell className="text-center text-sm">{item.baseline.precision.toFixed(2)}</TableCell>
                    <TableCell className="text-center text-sm">{item.baseline.recall.toFixed(2)}</TableCell>
                    <TableCell className="text-center text-sm border-r">{item.baseline.f1.toFixed(2)}</TableCell>
                    {/* Adaptive */}
                    <TableCell className="text-center text-sm font-semibold">{item.adaptive.accuracy.toFixed(2)}</TableCell>
                    <TableCell className="text-center text-sm font-semibold">{item.adaptive.precision.toFixed(2)}</TableCell>
                    <TableCell className="text-center text-sm font-semibold">{item.adaptive.recall.toFixed(2)}</TableCell>
                    <TableCell className="text-center text-sm font-semibold">{item.adaptive.f1.toFixed(2)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
