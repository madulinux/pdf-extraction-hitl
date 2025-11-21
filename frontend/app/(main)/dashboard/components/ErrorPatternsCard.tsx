"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, ChevronRight } from "lucide-react";
import type { ErrorPatterns } from "@/lib/types/dashboard.types";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { useState } from "react";

interface ErrorPatternsCardProps {
  data: ErrorPatterns;
}

export function ErrorPatternsCard({ data }: ErrorPatternsCardProps) {
  const [openFields, setOpenFields] = useState<Set<string>>(new Set());

  if (!data || !data.most_problematic_fields || data.most_problematic_fields.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        No error patterns detected - all extractions are accurate! 🎉
      </div>
    );
  }

  const toggleField = (fieldName: string) => {
    const newOpen = new Set(openFields);
    if (newOpen.has(fieldName)) {
      newOpen.delete(fieldName);
    } else {
      newOpen.add(fieldName);
    }
    setOpenFields(newOpen);
  };

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <AlertTriangle className="h-4 w-4" />
        <span>
          {data.total_unique_errors} field(s) with errors detected
        </span>
      </div>

      {/* Problematic Fields */}
      <div className="space-y-3">
        {data.most_problematic_fields.slice(0, 5).map((field) => {
          const isOpen = openFields.has(field.field_name);
          const errorRate = field.error_count;

          return (
            <Collapsible
              key={field.field_name}
              open={isOpen}
              onOpenChange={() => toggleField(field.field_name)}
            >
              <Card className="border-l-4 border-l-destructive">
                <CollapsibleTrigger className="w-full">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <ChevronRight
                          className={`h-4 w-4 transition-transform ${
                            isOpen ? "rotate-90" : ""
                          }`}
                        />
                        <div className="text-left">
                          <p className="font-semibold capitalize">
                            {field.field_name.replace(/_/g, " ")}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {field.error_count} errors
                          </p>
                        </div>
                      </div>
                      <Badge variant="destructive">
                        {errorRate} corrections
                      </Badge>
                    </div>
                  </CardContent>
                </CollapsibleTrigger>

                <CollapsibleContent>
                  <CardContent className="pt-0 pb-4 px-4">
                    <div className="space-y-3 mt-2">
                      <p className="text-xs font-medium text-muted-foreground">
                        Example Errors:
                      </p>
                      {field.examples.slice(0, 2).map((example, idx) => (
                        <div
                          key={idx}
                          className="bg-muted/50 rounded-lg p-3 space-y-2 text-sm"
                        >
                          <div>
                            <p className="text-xs text-muted-foreground mb-1">
                              Original (Incorrect):
                            </p>
                            <p className="font-mono text-xs bg-destructive/10 p-2 rounded">
                              {example.original || "(empty)"}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground mb-1">
                              Corrected:
                            </p>
                            <p className="font-mono text-xs bg-green-500/10 p-2 rounded">
                              {example.corrected}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </CollapsibleContent>
              </Card>
            </Collapsible>
          );
        })}
      </div>

      {/* Action Recommendation */}
      {data.most_problematic_fields.length > 0 && (
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4">
          <p className="text-sm font-medium mb-1">💡 Recommendation</p>
          <p className="text-xs text-muted-foreground">
            Focus improvement efforts on{" "}
            <span className="font-semibold">
              {data.most_problematic_fields[0].field_name.replace(/_/g, " ")}
            </span>{" "}
            which has the highest error rate. Consider reviewing feature
            extraction or adding more training examples.
          </p>
        </div>
      )}
    </div>
  );
}
