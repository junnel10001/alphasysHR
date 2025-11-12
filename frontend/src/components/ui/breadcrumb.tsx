import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { ChevronRight, Home } from 'lucide-react'

interface BreadcrumbItem {
  label: string
  href?: string
  current?: boolean
}

interface BreadcrumbProps {
  items: BreadcrumbItem[]
  className?: string
}

export function Breadcrumb({ items, className }: BreadcrumbProps) {
  return (
    <nav
      aria-label="Breadcrumb"
      className={cn("flex items-center space-x-1 text-sm", className)}
    >
      <ol className="flex items-center space-x-1">
        {items.map((item, index) => {
          const isLast = index === items.length - 1
          
          return (
            <li key={index} className="flex items-center">
              {index > 0 && (
                <ChevronRight className="mx-2 h-4 w-4 text-muted-foreground flex-shrink-0" />
              )}
              {item.href && !isLast ? (
                <Link
                  href={item.href}
                  prefetch={false}
                  className={cn(
                    "flex items-center px-2 py-1 rounded-md transition-all duration-200 hover:bg-alphasys/10 hover:text-alphasys-foreground",
                    "text-muted-foreground hover:text-alphasys-foreground"
                  )}
                  aria-current={item.current ? "page" : undefined}
                >
                  {item.label}
                </Link>
              ) : (
                <span
                  className={cn(
                    "flex items-center px-2 py-1",
                    isLast
                      ? "text-foreground font-medium"
                      : "text-muted-foreground"
                  )}
                  aria-current={item.current ? "page" : undefined}
                >
                  {item.label}
                </span>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

// Hook to generate breadcrumbs based on current path
export function useBreadcrumbs() {
  // Only access pathname on client side
  const pathname = typeof window !== 'undefined' ? usePathname() : ''
  
  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    // Add Home as first item
    const breadcrumbs: BreadcrumbItem[] = [{
      label: 'Home',
      href: '/',
      current: false
    }]
    
    // Remove leading slash and split path
    const pathSegments = pathname.replace(/^\/|\/$/g, '').split('/')
    
    // Special handling for System Configuration breadcrumbs
    if (pathname.startsWith('/system-config')) {
      // Add System Configuration as second breadcrumb
      breadcrumbs.push({
        label: 'System Configuration',
        href: '/system-config',
        current: pathSegments.length === 1 && pathSegments[0] === 'system-config'
      })
      
      // If we have more segments beyond system-config
      if (pathSegments.length > 1) {
        // Handle case where we're in a definitions sub-path
        if (pathSegments[1] === 'definitions') {
          // Skip "definitions" and add the final page directly
          if (pathSegments.length > 2) {
            const finalSegment = pathSegments[pathSegments.length - 1]
            const label = finalSegment
              .split('-')
              .map(word => word.charAt(0).toUpperCase() + word.slice(1))
              .join(' ')
            
            breadcrumbs.push({
              label,
              href: undefined, // Current page, no link
              current: true
            })
          }
        } else {
          // For non-definition paths, add the current segment
          const segment = pathSegments[pathSegments.length - 1]
          const label = segment
            .split('-')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ')
          
          breadcrumbs.push({
            label,
            href: undefined, // Current page, no link
            current: true
          })
        }
      }
    } else {
      // Default behavior for non-system-config pages
      pathSegments.forEach((segment, index) => {
        if (!segment) return
        
        // Build href incrementally
        const href = '/' + pathSegments.slice(0, index + 1).join('/')
        
        // Generate label from segment
        const label = segment
          .split('-')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ')
        
        // Check if this is the current page
        const isCurrent = index === pathSegments.length - 1
        
        breadcrumbs.push({
          label,
          href: isCurrent ? undefined : href,
          current: isCurrent
        })
      })
    }
    
    return breadcrumbs
  }
  
  return {
    pathname: pathname || '',
    breadcrumbs: generateBreadcrumbs()
  }
}