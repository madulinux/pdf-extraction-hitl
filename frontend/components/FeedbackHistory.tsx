'use client';

import React from 'react';
import { FeedbackRecord } from '@/lib/types/extraction.types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, Clock, ArrowRight } from 'lucide-react';

interface FeedbackHistoryProps {
  feedbackHistory: FeedbackRecord[];
}

export default function FeedbackHistory({ feedbackHistory }: FeedbackHistoryProps) {
  if (!feedbackHistory || feedbackHistory.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Riwayat Koreksi</CardTitle>
          <CardDescription>Belum ada koreksi untuk dokumen ini</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // Group by field_name
  const groupedFeedback = feedbackHistory.reduce((acc, feedback) => {
    if (!acc[feedback.field_name]) {
      acc[feedback.field_name] = [];
    }
    acc[feedback.field_name].push(feedback);
    return acc;
  }, {} as Record<string, FeedbackRecord[]>);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('id-ID', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Riwayat Koreksi</CardTitle>
        <CardDescription>
          {feedbackHistory.length} koreksi untuk {Object.keys(groupedFeedback).length} field
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {Object.entries(groupedFeedback).map(([fieldName, records]) => (
          <div key={fieldName} className="border rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-sm uppercase text-muted-foreground">
                {fieldName}
              </h4>
              <Badge variant={records[0].used_for_training ? "default" : "secondary"}>
                {records[0].used_for_training ? (
                  <><CheckCircle2 className="w-3 h-3 mr-1" /> Digunakan untuk Training</>
                ) : (
                  <><Clock className="w-3 h-3 mr-1" /> Belum Digunakan</>
                )}
              </Badge>
            </div>

            {records.map((record, index) => (
              <div key={record.id} className="space-y-2">
                {index > 0 && <div className="border-t pt-2" />}
                
                <div className="flex items-start gap-3">
                  <div className="flex-1 space-y-1">
                    {record.original_value && (
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-muted-foreground">Original:</span>
                        <span className="line-through text-red-600">{record.original_value}</span>
                      </div>
                    )}
                    
                    <div className="flex items-center gap-2 text-sm">
                      <ArrowRight className="w-4 h-4 text-muted-foreground" />
                      <span className="text-muted-foreground">Koreksi:</span>
                      <span className="font-medium text-green-600">{record.corrected_value}</span>
                    </div>

                    {record.confidence_score !== null && (
                      <div className="text-xs text-muted-foreground">
                        Confidence: {(record.confidence_score * 100).toFixed(1)}%
                      </div>
                    )}
                  </div>

                  <div className="text-xs text-muted-foreground text-right">
                    <div>{formatDate(record.created_at)}</div>
                    {record.updated_at !== record.created_at && (
                      <div className="text-xs text-amber-600">
                        Updated: {formatDate(record.updated_at)}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
