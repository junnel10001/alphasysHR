import React from 'react'
import { ChartTooltipProps } from './types'

export function ChartTooltip({ active, payload, label, formatter }: ChartTooltipProps) {
  if (active && payload && payload.length) {
    return (
      <div
        className="bg-card border border-border rounded-lg shadow-lg p-3"
        style={{
          '--tooltip-bg': 'var(--card)',
          '--tooltip-border': 'var(--border)',
          '--tooltip-text': 'var(--foreground)'
        } as React.CSSProperties}
      >
        <p className="font-medium text-foreground">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            {entry.name}: {entry.value}
          </p>
        ))}
      </div>
    )
  }
  return null
}