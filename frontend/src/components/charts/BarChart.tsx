import React from 'react'
import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import { cn } from '@/lib/utils'
import { BarChartProps } from './types'
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

export function BarChart({
  data,
  title,
  height = 300,
  className,
  colors = alphaSysColors,
  showLegend = true,
  showGrid = true,
  animationDuration = 1000,
  barSize = 20,
  stackId,
  fill
}: BarChartProps) {
  return (
    <ChartContainer className={className} height={height}>
      {title && (
        <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--foreground)' }}>{title}</h3>
      )}
      <ResponsiveContainer width="100%" height={height - (title ? 60 : 20)}>
        <RechartsBarChart
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
          
          {/* Single bar case for simplicity */}
          <Bar
            dataKey="value"
            fill={fill || colors[0]}
            radius={[4, 4, 0, 0]}
            barSize={barSize}
            stackId={stackId}
            isAnimationActive={true}
            animationDuration={animationDuration}
          />
        </RechartsBarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}