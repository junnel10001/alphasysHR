'use client'

import React from 'react'
import { Breadcrumb, useBreadcrumbs } from '@/components/ui/breadcrumb'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface PageTemplateProps {
  children: React.ReactNode
  title?: string
  description?: string
  breadcrumbs?: Array<{ label: string; href?: string }>
  className?: string
  headerActions?: React.ReactNode
  cardClassName?: string
}

export function PageTemplate({
  children,
  title,
  description,
  breadcrumbs,
  className,
  headerActions,
  cardClassName
}: PageTemplateProps) {
  // Only use breadcrumbs on client side to prevent SSR issues
  const currentBreadcrumbs = typeof window !== 'undefined' ? useBreadcrumbs().breadcrumbs : []
  
  // Use provided breadcrumbs or fall back to current path breadcrumbs
  const displayBreadcrumbs = breadcrumbs || currentBreadcrumbs

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header Section */}
      {(title || description || displayBreadcrumbs.length > 0 || headerActions) && (
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex-1 min-w-0">
            {displayBreadcrumbs.length > 0 && (
              <Breadcrumb items={displayBreadcrumbs} className="mb-2" />
            )}
            {title && (
              <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
            )}
            {description && (
              <p className="text-muted-foreground mt-1">{description}</p>
            )}
          </div>
          {headerActions && (
            <div className="flex-shrink-0">
              {headerActions}
            </div>
          )}
        </div>
      )}

      {/* Main Content */}
      <Card className={cn('border-0 shadow-none', cardClassName)}>
        <CardContent className="p-0">
          {children}
        </CardContent>
      </Card>
    </div>
  )
}

// Sub-components for different content sections
interface PageSectionProps {
  children: React.ReactNode
  title?: string
  description?: string
  className?: string
}

export function PageSection({ children, title, description, className }: PageSectionProps) {
  return (
    <div className={cn('space-y-4', className)}>
      {(title || description) && (
        <div className="space-y-2">
          {title && <h3 className="text-lg font-semibold">{title}</h3>}
          {description && <p className="text-sm text-muted-foreground">{description}</p>}
        </div>
      )}
      {children}
    </div>
  )
}

interface PageGridProps {
  children: React.ReactNode
  cols?: 1 | 2 | 3 | 4
  gap?: 'sm' | 'md' | 'lg'
  className?: string
}

export function PageGrid({ children, cols = 1, gap = 'md', className }: PageGridProps) {
  const gapClasses = {
    sm: 'gap-2',
    md: 'gap-4',
    lg: 'gap-6'
  }

  const colClasses = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 sm:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'
  }

  return (
    <div className={cn('grid', colClasses[cols], gapClasses[gap], className)}>
      {children}
    </div>
  )
}

interface PageActionsProps {
  children: React.ReactNode
  className?: string
}

export function PageActions({ children, className }: PageActionsProps) {
  return (
    <div className={cn('flex flex-col sm:flex-row gap-3', className)}>
      {children}
    </div>
  )
}

interface PageAlertProps {
  children: React.ReactNode
  variant?: 'default' | 'destructive' | 'warning' | 'success'
  className?: string
}

export function PageAlert({ children, variant = 'default', className }: PageAlertProps) {
  const variantClasses = {
    default: 'bg-blue-50 text-blue-700 border-blue-200',
    destructive: 'bg-red-50 text-red-700 border-red-200',
    warning: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    success: 'bg-green-50 text-green-700 border-green-200'
  }

  return (
    <div className={cn(
      'rounded-md border p-4',
      variantClasses[variant],
      className
    )}>
      {children}
    </div>
  )
}