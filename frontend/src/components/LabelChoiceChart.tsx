"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
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
    <div className="mt-4">
      <p className="mb-2 text-xs text-neutral-500 dark:text-neutral-400">
        Bar = cost-model enrolment rate − burden-model enrolment rate.
        Negative means the cost-trained model enrols that group{" "}
        <em>less</em> often.
      </p>
      <div className="h-80 w-full overflow-x-auto">
      <ResponsiveContainer width="100%" height="100%" minWidth={480}>
        <BarChart data={data} layout="vertical" margin={{ left: 24, right: 24 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.25} />
          <XAxis
            type="number"
            label={{ value: "gap (percentage points)", position: "insideBottom", offset: -5 }}
          />
          <YAxis type="category" dataKey="race" width={80} />
          <Tooltip formatter={(value) => [`${value}pp`, "gap (cost − burden)"]} />
          <Bar dataKey="gap" radius={4}>
            {data.map((entry) => (
              <Cell key={entry.race} fill={entry.race === TARGET_STRATUM ? "#dc2626" : "#94a3b8"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      </div>
    </div>
  );
}
