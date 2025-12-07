"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, MessageSquare, Clock } from "lucide-react";
import { RecentActivity } from "@/lib/api/dashboard.api";
import { formatDistanceToNow } from "date-fns";

interface RecentActivityListProps {
  activities: RecentActivity[];
}

export function RecentActivityList({ activities }: RecentActivityListProps) {
  const getActivityIcon = (type: string) => {
    return type === "document" ? (
      <FileText className="h-4 w-4" />
    ) : (
      <MessageSquare className="h-4 w-4" />
    );
  };

  const getActivityColor = (type: string) => {
    return type === "document" ? "text-blue-600" : "text-green-600";
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
    } catch {
      return timestamp;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Recent Activity
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {activities.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              No recent activity
            </p>
          ) : (
            activities.map((activity) => (
              <div
                key={`${activity.type}-${activity.id}`}
                className="flex items-start gap-3 p-3 rounded-lg border hover:bg-muted/50 transition-colors"
              >
                <div className={`mt-0.5 ${getActivityColor(activity.type)}`}>
                  {getActivityIcon(activity.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="outline" className="text-xs">
                      {activity.template_name}
                    </Badge>
                    <Badge
                      variant={
                        activity.type === "document" ? "default" : "secondary"
                      }
                      className="text-xs"
                    >
                      {activity.type}
                    </Badge>
                  </div>
                  <p className="text-sm font-medium mt-1 truncate">
                    {activity.type === "document"
                      ? activity.filename
                      : `Feedback on ${activity.field_name}`}
                  </p>
                  {activity.type === "document" && activity.status && (
                    <p className="text-xs text-muted-foreground">
                      Status: {activity.status}
                      {activity.validated && " • Validated"}
                    </p>
                  )}
                  {activity.type === "feedback" && activity.filename && (
                    <p className="text-xs text-muted-foreground truncate">
                      Document: {activity.filename}
                    </p>
                  )}
                </div>
                <div className="text-xs text-muted-foreground whitespace-nowrap">
                  {formatTimestamp(activity.timestamp)}
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
