'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

interface TabsProps extends React.HTMLAttributes<HTMLDivElement> {
  defaultValue?: string
  value?: string
  onValueChange?: (value: string) => void
}

interface TabsListProps extends React.HTMLAttributes<HTMLDivElement> {}

interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string
}

interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string
}

/**
 * Simple Tabs implementation for the employee wizard.
 * It mirrors the API used in the page component:
 *   <Tabs defaultValue="personal">
 *     <TabsList>
 *       <TabsTrigger value="personal">Personal Info</TabsTrigger>
 *       ...
 *     </TabsList>
 *     <TabsContent value="personal">...</TabsContent>
 *   </Tabs>
 */
export function Tabs({
  defaultValue,
  value: controlledValue,
  onValueChange,
  className,
  children,
  ...props
}: TabsProps) {
  const [value, setValue] = React.useState<string>(defaultValue ?? '')

  const current = controlledValue ?? value

  const handleChange = (newValue: string) => {
    if (!controlledValue) {
      setValue(newValue)
    }
    onValueChange?.(newValue)
  }

  return (
    <div className={cn('flex flex-col', className)} {...props}>
      {React.Children.map(children, child => {
        if (!React.isValidElement(child)) return child
        if (child.type === TabsList) {
          return React.cloneElement(child as React.ReactElement<any>, {
            onValueChange: handleChange,
            value: current,
          })
        }
        if (child.type === TabsContent) {
          return (child as React.ReactElement<any>).props.value === current
            ? child
            : null
        }
        return child
      })}
    </div>
  )
}

export function TabsList({
  className,
  children,
  onValueChange,
  value,
  ...props
}: TabsListProps & {
  onValueChange?: (value: string) => void
  value?: string
}) {
  return (
    <div
      className={cn('flex space-x-2', className)}
      {...props}
    >
      {React.Children.map(children, child => {
        if (!React.isValidElement(child)) return child
        if (child.type === TabsTrigger) {
          const trigger = child as React.ReactElement<TabsTriggerProps>
          const isActive = trigger.props.value === value
          return React.cloneElement(trigger, {
            className: cn(
              'px-3 py-1 rounded-md text-sm font-medium',
              isActive
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            ),
            onClick: () => onValueChange?.(trigger.props.value),
          })
        }
        return child
      })}
    </div>
  )
}

export function TabsTrigger({
  className,
  value,
  ...props
}: TabsTriggerProps) {
  return (
    <button
      type="button"
      value={value}
      className={cn('focus:outline-none', className)}
      {...props}
    />
  )
}

export function TabsContent({
  className,
  value,
  children,
  ...props
}: TabsContentProps) {
  return (
    <div className={cn('mt-4', className)} {...props}>
      {children}
    </div>
  )
}