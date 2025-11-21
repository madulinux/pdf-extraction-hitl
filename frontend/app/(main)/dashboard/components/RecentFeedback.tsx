"use client";

import { formatDistanceToNow } from 'date-fns';
import { Badge } from "@/components/ui/badge";
import { ArrowRight } from "lucide-react";
import type { FeedbackItem } from "@/lib/types/dashboard.types";

interface RecentFeedbackProps {
  data: FeedbackItem[];
}

export function RecentFeedback({ data }: RecentFeedbackProps) {
  if (!data || data.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        No recent feedback available
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {data.map((item, index) => (
        <div key={index} className="p-4 rounded-lg border hover:bg-muted/50 transition-colors">
          <div className="flex items-start justify-between mb-2">
            <Badge variant="outline" className="capitalize">
              {item.field_name.replace(/_/g, " ")}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {formatDistanceToNow(new Date(item.timestamp), { addSuffix: true })}
            </span>
          </div>
          
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground line-through max-w-[200px] truncate">
              {item.original_value || "(empty)"}
            </span>
            <ArrowRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            <span className="font-medium text-foreground max-w-[200px] truncate">
              {item.corrected_value}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
