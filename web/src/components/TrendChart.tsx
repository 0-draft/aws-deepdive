import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface Props {
  data: { week: string; count: number }[];
}

export default function TrendChart({ data }: Props) {
  if (!data || data.length === 0) {
    return (
      <div className="h-48 w-full flex items-center justify-center text-xs text-white/30 font-mono">
        no data yet
      </div>
    );
  }
  return (
    <div className="h-48 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="awsdd-grad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#60a5fa" stopOpacity={0.55} />
              <stop offset="100%" stopColor="#60a5fa" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#ffffff14" vertical={false} />
          <XAxis
            dataKey="week"
            tick={{ fill: "#ffffff80", fontSize: 10, fontFamily: "monospace" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#ffffff80", fontSize: 10, fontFamily: "monospace" }}
            axisLine={false}
            tickLine={false}
            width={28}
          />
          <Tooltip
            contentStyle={{
              background: "#111",
              border: "1px solid #ffffff20",
              borderRadius: 6,
              fontSize: 12,
            }}
            labelStyle={{ color: "#fff" }}
            cursor={{ stroke: "#ffffff20" }}
          />
          <Area
            type="monotone"
            dataKey="count"
            stroke="#60a5fa"
            strokeWidth={2}
            fill="url(#awsdd-grad)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
