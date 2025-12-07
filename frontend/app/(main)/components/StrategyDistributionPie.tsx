"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { StrategyDistribution } from "@/lib/api/dashboard.api";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";

interface StrategyDistributionPieProps {
  data: StrategyDistribution[];
}

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

export function StrategyDistributionPie({
  data,
}: StrategyDistributionPieProps) {
  const chartData = data.map((item) => ({
    name: item.strategy === "rule_based" ? "Rule-Based" : "CRF",
    value: item.count,
    accuracy: (item.avg_accuracy * 100).toFixed(1),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Strategy Distribution</CardTitle>
        <CardDescription>
          Usage of extraction strategies across all templates
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) =>
                `${name}: ${(percent * 100).toFixed(0)}%`
              }
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[index % COLORS.length]}
                />
              ))}
            </Pie>
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-background border rounded-lg p-3 shadow-lg">
                      <p className="font-semibold">{data.name}</p>
                      <p className="text-sm text-muted-foreground">
                        Count: {data.value}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Avg Accuracy: {data.accuracy}%
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
      </CardContent>
    </Card>
  );
}
