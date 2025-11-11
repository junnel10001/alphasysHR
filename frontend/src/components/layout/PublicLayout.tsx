'use client'

import React from 'react'
import Link from 'next/link'
import { AlphaSysLogo } from '@/components/ui/logo'
import { Button } from '@/components/ui/button'
import { ArrowLeft } from 'lucide-react'

interface PublicLayoutProps {
  children: React.ReactNode
  showBackButton?: boolean
  backButtonHref?: string
  backButtonLabel?: string
  title?: string
  description?: string
}

export function PublicLayout({
  children,
  showBackButton = false,
  backButtonHref = '/',
  backButtonLabel = 'Back to Home',
  title,
  description
}: PublicLayoutProps) {
  // Prevent hydration mismatch by ensuring consistent theme handling
  const [mounted, setMounted] = React.useState(false)

  React.useEffect(() => {
    setMounted(true)
    return () => {}
  }, [])

  if (!mounted) {
    // Return a minimal version during SSR to prevent hydration mismatch
    return (
      <div className="min-h-screen bg-background flex flex-col">
        {/* Header */}
        <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
          <div className="container mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center">
                <AlphaSysLogo size="sm" />
            </div>
            
            <div className="flex items-center space-x-2">
              {showBackButton && (
                <Button variant="ghost" size="sm" asChild>
                  <Link href={backButtonHref} className="flex items-center" prefetch={false}>
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    {backButtonLabel}
                  </Link>
                </Button>
              )}
              {/* Don't render ThemeToggle during SSR */}
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 flex items-center justify-center p-4">
          <div className="w-full max-w-md space-y-6">
            {title && (
              <div className="text-center space-y-2">
                <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
                {description && (
                  <p className="text-muted-foreground">{description}</p>
                )}
              </div>
            )}
            {children}
          </div>
        </main>

        {/* Footer */}
        <footer className="border-t bg-background py-6">
          <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
            <p>&copy; 2025. All rights reserved.</p>
          </div>
        </footer>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center">
              <AlphaSysLogo size="sm" />
          </div>
          
          <div className="flex items-center space-x-2">
            {showBackButton && (
              <Button variant="ghost" size="sm" asChild>
                <Link href={backButtonHref} className="flex items-center" prefetch={false}>
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  {backButtonLabel}
                </Link>
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md space-y-6">
          {title && (
            <div className="text-center space-y-2">
              <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
              {description && (
                <p className="text-muted-foreground">{description}</p>
              )}
            </div>
          )}
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t bg-background py-6">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>&copy; 2025. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}