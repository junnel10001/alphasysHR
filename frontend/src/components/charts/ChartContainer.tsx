import React from 'react'
import { cn } from '@/lib/utils'
import { ChartContainerProps } from './types'

export function ChartContainer({ children, className, height = 300 }: ChartContainerProps) {
  return (
    <div
      className={cn(
        "w-full bg-card border border-border rounded-lg p-4",
        className
      )}
      style={{
        height: typeof height === 'number' ? `${height}px` : height,
        '--chart-bg': 'var(--card)',
        '--chart-border': 'var(--border)',
        '--chart-text': 'var(--foreground)'
      } as React.CSSProperties}
    >
      {children}
    </div>
  )
}