"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { format } from 'date-fns';
import type { AccuracyDataPoint } from '@/lib/types/dashboard.types';

interface AccuracyChartProps {
  data: AccuracyDataPoint[];
}

export function AccuracyChart({ data }: AccuracyChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[300px] text-muted-foreground">
        No data available
      </div>
    );
  }

  // Limit to last 100 documents for better visualization
  const limitedData = data.slice(-100);

  // Calculate moving average (window of 5)
  const calculateMovingAverage = (data: AccuracyDataPoint[], window: number = 5) => {
    return data.map((point, index) => {
      const start = Math.max(0, index - window + 1);
      const subset = data.slice(start, index + 1);
      const avg = subset.reduce((sum, p) => sum + p.accuracy, 0) / subset.length;
      return avg;
    });
  };

  const movingAvg = calculateMovingAverage(limitedData);

  // Format data for chart with time-based X-axis
  const chartData = limitedData.map((point, index) => ({
    // Use timestamp for X-axis (more meaningful than "Doc 1, Doc 2")
    date: format(new Date(point.timestamp), 'MMM dd'),
    fullDate: format(new Date(point.timestamp), 'MMM dd, yyyy HH:mm'),
    accuracy: parseFloat((point.accuracy * 100).toFixed(1)),
    movingAvg: parseFloat((movingAvg[index] * 100).toFixed(1)),
    documentId: point.document_id,
    totalFields: point.total_fields,
    correctFields: point.correct_fields,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="date" 
          tick={{ fontSize: 11 }}
          interval="preserveStartEnd"
          minTickGap={30}
        />
        <YAxis 
          domain={[0, 100]}
          tick={{ fontSize: 12 }}
          label={{ value: 'Accuracy (%)', angle: -90, position: 'insideLeft' }}
        />
        <Tooltip 
          content={({ active, payload }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload;
              return (
                <div className="bg-background border rounded-lg p-3 shadow-lg">
                  <p className="font-semibold">Document #{data.documentId}</p>
                  <p className="text-sm text-muted-foreground">
                    {data.fullDate}
                  </p>
                  <div className="mt-2 space-y-1">
                    <p className="text-lg font-bold text-primary">
                      {data.accuracy}% Accuracy
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {data.correctFields}/{data.totalFields} fields correct
                    </p>
                    {payload.length > 1 && (
                      <p className="text-xs text-blue-500">
                        Moving Avg: {data.movingAvg}%
                      </p>
                    )}
                  </div>
                </div>
              );
            }
            return null;
          }}
        />
        <Legend />
        <Line 
          type="monotone" 
          dataKey="accuracy" 
          stroke="hsl(var(--primary))" 
          strokeWidth={2}
          dot={{ r: 3 }}
          activeDot={{ r: 6 }}
          name="Accuracy"
        />
        <Line 
          type="monotone" 
          dataKey="movingAvg" 
          stroke="hsl(var(--chart-2))" 
          strokeWidth={2}
          strokeDasharray="5 5"
          dot={false}
          name="Moving Average (5-doc)"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
