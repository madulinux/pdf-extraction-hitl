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
import type { FieldPerformance } from "@/lib/types/dashboard.types";

interface FieldPerformanceTableProps {
  data: Record<string, FieldPerformance>;
}

export function FieldPerformanceTable({ data }: FieldPerformanceTableProps) {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        No field performance data available
      </div>
    );
  }

  // Sort by accuracy (descending)
  const sortedFields = Object.entries(data).sort(
    ([, a], [, b]) => b.accuracy - a.accuracy
  );

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 0.9) return "text-green-600";
    if (accuracy >= 0.7) return "text-yellow-600";
    return "text-red-600";
  };

  const getAccuracyBadge = (accuracy: number) => {
    if (accuracy >= 0.9) return "default";
    if (accuracy >= 0.7) return "secondary";
    return "destructive";
  };

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Field Name</TableHead>
            <TableHead>Accuracy</TableHead>
            <TableHead className="text-center">Total</TableHead>
            <TableHead className="text-center">Correct</TableHead>
            <TableHead className="text-center">Errors</TableHead>
            <TableHead>Confidence</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedFields.map(([fieldName, stats]) => (
            <TableRow key={fieldName}>
              <TableCell className="font-medium capitalize">
                {fieldName.replace(/_/g, " ")}
              </TableCell>
              <TableCell>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`font-bold ${getAccuracyColor(
                        stats.accuracy
                      )}`}
                    >
                      {stats.accuracy < 0
                        ? (0).toFixed(1)
                        : (stats.accuracy * 100).toFixed(1)}
                      %
                    </span>
                    <Badge
                      variant={getAccuracyBadge(stats.accuracy)}
                      className="text-xs"
                    >
                      {stats.accuracy >= 0.9
                        ? "Excellent"
                        : stats.accuracy >= 0.7
                        ? "Good"
                        : "Needs Improvement"}
                    </Badge>
                  </div>
                  <Progress value={stats.accuracy * 100} className="h-1" />
                </div>
              </TableCell>
              <TableCell className="text-center">
                <Badge variant="outline">{stats.total_extractions}</Badge>
              </TableCell>
              <TableCell className="text-center">
                <Badge variant="default" className="bg-green-500">
                  {stats.correct_extractions < 0 ? 0 : stats.correct_extractions}
                </Badge>
              </TableCell>
              <TableCell className="text-center">
                <Badge
                  variant={stats.corrections > 0 ? "destructive" : "outline"}
                >
                  {stats.corrections}
                </Badge>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Progress
                    value={stats.avg_confidence * 100}
                    className="h-2 flex-1"
                  />
                  <span className="text-sm text-muted-foreground min-w-[3rem]">
                    {(stats.avg_confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
