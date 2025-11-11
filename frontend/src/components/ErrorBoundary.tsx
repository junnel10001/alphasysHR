'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { AlertTriangle, Home, ArrowLeft, RefreshCw, FileX } from 'lucide-react'
import { PublicLayout } from '@/components/layout'

interface ErrorBoundaryProps {
  children: React.ReactNode
  error?: Error
  type?: 'general' | '404'
}

export function ErrorBoundary({ children, error, type = 'general' }: ErrorBoundaryProps) {
  const router = useRouter()
  const [hasError, setHasError] = useState(false)

  useEffect(() => {
    if (error) {
      console.error('Error caught by boundary:', error)
      setHasError(true)
    }
  }, [error])

  if (hasError || error) {
    const is404 = type === '404' || error?.message?.includes('404') || error?.message?.includes('not found')
    
    return (
      <PublicLayout
        title={is404 ? 'Page Not Found' : 'Something went wrong'}
        description={is404
          ? 'The page you\'re looking for doesn\'t exist or has been moved.'
          : 'An error occurred while loading this page.'
        }
      >
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-red-100">
              {is404 ? (
                <FileX className="h-6 w-6 text-red-600" />
              ) : (
                <AlertTriangle className="h-6 w-6 text-red-600" />
              )}
            </div>
            <CardTitle className="mt-4">
              {is404 ? 'Page Not Found' : 'Something went wrong'}
            </CardTitle>
            <CardDescription>
              {is404
                ? 'The page you\'re looking for doesn\'t exist or has been moved.'
                : 'An error occurred while loading this page.'
              }
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col items-center space-y-4">
            <p className="text-sm text-muted-foreground text-center">
              {is404
                ? 'Error 404 - The requested resource could not be found'
                : error?.message || 'An unexpected error occurred'
              }
            </p>
            <div className="flex space-x-2 w-full">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => router.push('/')}
              >
                <Home className="h-4 w-4 mr-2" />
                Go to Home
              </Button>
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => router.back()}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Go Back
              </Button>
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => router.refresh()}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </CardContent>
        </Card>
      </PublicLayout>
    )
  }

  return <>{children}</>
}