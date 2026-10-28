"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { LabelChoiceRow } from "@/lib/types";

const TARGET_STRATUM = "black";

export function LabelChoiceChart({ rows }: { rows: LabelChoiceRow[] }) {
  const sorted = [...rows].sort((a, b) => a.gap_percentage_points - b.gap_percentage_points);
  const data = sorted.map((row) => ({
    race: row.race,
    gap: Number(row.gap_percentage_points.toFixed(1)),
  }));

  return (
    <div className="mt-4 h-80 w-full overflow-x-auto">
      <ResponsiveContainer width="100%" height="100%" minWidth={480}>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 32, bottom: 24, top: 8 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#94a3b8" opacity={0.3} />
          <XAxis
            type="number"
            tick={{ fill: "#64748b", fontSize: 12 }}
            tickFormatter={(v: number) => `${v}pp`}
            label={{ value: "gap (percentage points)", position: "insideBottom", offset: -12, fill: "#64748b", fontSize: 12 }}
          />
          <YAxis
            type="category"
            dataKey="race"
            width={90}
            tick={{ fill: "#475569", fontSize: 13 }}
            tickFormatter={(v: string) => v.charAt(0).toUpperCase() + v.slice(1)}
          />
          <ReferenceLine x={0} stroke="#475569" />
          <Tooltip
            cursor={{ fill: "rgba(13,148,136,0.08)" }}
            formatter={(value) => [`${value}pp`, "cost − burden"]}
          />
          <Bar dataKey="gap" radius={4} barSize={22}>
            {data.map((entry) => (
              <Cell key={entry.race} fill={entry.race === TARGET_STRATUM ? "#dc2626" : "#94a3b8"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
