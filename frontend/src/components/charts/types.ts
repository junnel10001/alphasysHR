export interface ChartDataPoint {
  name: string
  value: number
  date?: string
  category?: string
}

export interface ChartProps {
  data: ChartDataPoint[]
  title?: string
  height?: number
  className?: string
  colors?: string[]
  showLegend?: boolean
  showGrid?: boolean
  animationDuration?: number
}

export interface LineChartProps extends ChartProps {
  strokeDasharray?: string
  strokeWidth?: number
  dot?: boolean
  activeDot?: boolean
}

export interface BarChartProps extends ChartProps {
  barSize?: number
  stackId?: string
  fill?: string
}

export interface PieChartProps extends ChartProps {
  cx?: number | string
  cy?: number | string
  innerRadius?: number | string
  outerRadius?: number | string
  paddingAngle?: number
  dataKey?: string
}

export interface AreaChartProps extends ChartProps {
  fillOpacity?: number
  strokeDasharray?: string
  strokeWidth?: number
}

export interface ChartContainerProps {
  children: React.ReactNode
  className?: string
  height?: number | string
}

export interface ChartTooltipProps {
  active?: boolean
  payload?: any[]
  label?: string
  formatter?: (value: any, name: string, props: any) => [string, string]
}