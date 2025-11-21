"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Badge } from "@/components/ui/badge";

interface StrategyDistributionProps {
  data: Record<string, number>;
  detailed?: boolean;
}

const COLORS = {
  'hybrid-crf': 'hsl(var(--chart-1))',
  'hybrid-position_based': 'hsl(var(--chart-2))',
  'hybrid-rule_based': 'hsl(var(--chart-3))',
  'crf': 'hsl(var(--chart-4))',
  'position-based': 'hsl(var(--chart-5))',
  'rule-based': 'hsl(var(--chart-6))',
};

export function StrategyDistribution({ data, detailed = false }: StrategyDistributionProps) {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        No strategy data available
      </div>
    );
  }

  // Prepare data for pie chart
  const total = Object.values(data).reduce((sum, count) => sum + count, 0);
  const chartData = Object.entries(data).map(([name, value]) => ({
    name: name.replace('hybrid-', '').replace(/_/g, ' '),
    value,
    percentage: ((value / total) * 100).toFixed(1),
    fullName: name,
  }));

  // Sort by value descending
  chartData.sort((a, b) => b.value - a.value);

  const getColor = (strategyName: string) => {
    return COLORS[strategyName as keyof typeof COLORS] || 'hsl(var(--muted))';
  };

  if (detailed) {
    return (
      <div className="space-y-6">
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ percentage }) => `${percentage}%`}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getColor(entry.fullName)} />
              ))}
            </Pie>
            <Tooltip 
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-background border rounded-lg p-3 shadow-lg">
                      <p className="font-semibold capitalize">{data.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {data.value} extractions ({data.percentage}%)
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>

        <div className="space-y-3">
          <h4 className="font-semibold text-sm">Strategy Breakdown</h4>
          {chartData.map((item) => (
            <div key={item.fullName} className="flex items-center justify-between p-3 rounded-lg border">
              <div className="flex items-center gap-3">
                <div 
                  className="w-4 h-4 rounded-full" 
                  style={{ backgroundColor: getColor(item.fullName) }}
                />
                <span className="font-medium capitalize">{item.name}</span>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant="secondary">{item.value} uses</Badge>
                <span className="text-sm text-muted-foreground min-w-[3rem] text-right">
                  {item.percentage}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={250}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percentage }) => `${name}: ${percentage}%`}
          outerRadius={80}
          fill="#8884d8"
          dataKey="value"
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={getColor(entry.fullName)} />
          ))}
        </Pie>
        <Tooltip 
          content={({ active, payload }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload;
              return (
                <div className="bg-background border rounded-lg p-3 shadow-lg">
                  <p className="font-semibold capitalize">{data.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {data.value} extractions ({data.percentage}%)
                  </p>
                </div>
              );
            }
            return null;
          }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
