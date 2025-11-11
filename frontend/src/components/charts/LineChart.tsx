import React from 'react'
import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import { cn } from '@/lib/utils'
import { LineChartProps } from './types'
import { ChartContainer } from './ChartContainer'
import { ChartTooltip } from './ChartTooltip'

const alphaSysColors = [
  '#3B82F6', // Blue
  '#10B981', // Green
  '#F59E0B', // Amber
  '#EF4444', // Red
  '#8B5CF6', // Purple
  '#06B6D4', // Cyan
  '#F97316', // Orange
  '#84CC16', // Lime
]

export function LineChart({
  data,
  title,
  height = 300,
  className,
  colors = alphaSysColors,
  showLegend = true,
  showGrid = true,
  animationDuration = 1000,
  strokeDasharray,
  strokeWidth = 2,
  dot = true,
  activeDot = true
}: LineChartProps) {
  return (
    <ChartContainer className={className} height={height}>
      {title && (
        <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--foreground)' }}>{title}</h3>
      )}
      <ResponsiveContainer width="100%" height={height - (title ? 60 : 20)}>
        <RechartsLineChart
          data={data}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />}
          <XAxis
            dataKey="name"
            stroke="var(--muted-foreground)"
            tick={{ fontSize: 12 }}
            tickLine={false}
          />
          <YAxis
            stroke="var(--muted-foreground)"
            tick={{ fontSize: 12 }}
            tickLine={false}
          />
          <Tooltip content={<ChartTooltip />} />
          {showLegend && <Legend />}
          <Line
            type="monotone"
            dataKey="value"
            stroke={colors[0]}
            strokeWidth={strokeWidth}
            strokeDasharray={strokeDasharray}
            dot={dot}
            activeDot={{ r: 8, fill: colors[0] }}
            isAnimationActive={true}
            animationDuration={animationDuration}
          />
        </RechartsLineChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}