"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from "recharts";
import { LearningCurve } from "@/lib/api/dashboard.api";
import { Info } from "lucide-react";
import {
  Tooltip as UITooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface LearningCurvesChartProps {
  learningCurves: LearningCurve[];
}

const TEMPLATE_COLORS = {
  form_template: "#3b82f6",    // blue
  table_template: "#06b6d4",   // cyan
  letter_template: "#ef4444",  // red
  mixed_template: "#10b981",   // green
};

const TEMPLATE_LABELS = {
  form_template: "Form",
  table_template: "Table",
  letter_template: "Letter",
  mixed_template: "Mixed",
};

export function LearningCurvesChart({ learningCurves }: LearningCurvesChartProps) {
  // Transform data for recharts
  const maxBatches = Math.max(...learningCurves.map(lc => lc.batches.length));
  
  const chartData = Array.from({ length: maxBatches }, (_, i) => {
    const dataPoint: Record<string, number | string> = { batch: i };
    
    learningCurves.forEach(curve => {
      if (curve.batches[i]) {
        const key = curve.template_name;
        dataPoint[key] = curve.batches[i].accuracy;
      }
    });
    
    return dataPoint;
  });

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Learning Curves</CardTitle>
            <CardDescription>
              Accuracy progression across batches for all templates
            </CardDescription>
          </div>
          <TooltipProvider>
            <UITooltip>
              <TooltipTrigger asChild>
                <Info className="h-5 w-5 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent className="max-w-sm">
                <p className="font-semibold mb-2">Learning Curves</p>
                <p className="text-sm">
                  Shows how accuracy improves with each batch of documents processed.
                  Steeper curves indicate faster learning. The 95% target line represents
                  the desired accuracy threshold.
                </p>
                <p className="text-sm mt-2">
                  <strong>Batch Size:</strong> 5 documents per batch
                </p>
              </TooltipContent>
            </UITooltip>
          </TooltipProvider>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="batch" 
              label={{ value: 'Batch Number', position: 'insideBottom', offset: -5 }}
            />
            <YAxis 
              domain={[70, 102]}
              label={{ value: 'Accuracy (%)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip 
              formatter={(value: number) => `${value.toFixed(2)}%`}
              labelFormatter={(label) => `Batch ${label}`}
            />
            <Legend 
              verticalAlign="bottom"
              height={36}
              formatter={(value) => {
                const templateName = value as keyof typeof TEMPLATE_LABELS;
                return TEMPLATE_LABELS[templateName] || value;
              }}
            />
            
            {/* 95% Target Line */}
            <ReferenceLine 
              y={95} 
              stroke="#000" 
              strokeDasharray="5 5"
              label={{ value: '95% Target', position: 'right', fill: '#000', fontSize: 12 }}
            />
            
            {/* Lines for each template */}
            {learningCurves.map((curve) => (
              <Line
                key={curve.template_id}
                type="monotone"
                dataKey={curve.template_name}
                stroke={TEMPLATE_COLORS[curve.template_name as keyof typeof TEMPLATE_COLORS] || "#888"}
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
        
        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          {learningCurves.map((curve) => (
            <div key={curve.template_id} className="text-center p-3 bg-muted/50 rounded-lg">
              <div className="text-xs text-muted-foreground mb-1">
                {TEMPLATE_LABELS[curve.template_name as keyof typeof TEMPLATE_LABELS]}
              </div>
              <div className="text-2xl font-bold" style={{ 
                color: TEMPLATE_COLORS[curve.template_name as keyof typeof TEMPLATE_COLORS] 
              }}>
                {curve.final_accuracy.toFixed(1)}%
              </div>
              <div className="text-xs text-muted-foreground">
                +{curve.improvement.toFixed(1)}%
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
