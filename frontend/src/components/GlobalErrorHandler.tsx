'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { AlertTriangle, Home, ArrowLeft, RefreshCw } from 'lucide-react'

interface GlobalErrorHandlerProps {
  children: React.ReactNode
  error?: Error
}

export function GlobalErrorHandler({ children, error }: GlobalErrorHandlerProps) {
  const router = useRouter()

  useEffect(() => {
    if (error) {
      console.error('Global error caught:', error)
    }
  }, [error])

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-red-100">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
            <CardTitle className="mt-4">Page Not Found</CardTitle>
            <CardDescription>
              The page you're looking for doesn't exist or has been moved.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col items-center space-y-4">
            <p className="text-sm text-gray-600 text-center">
              Error 404 - The requested resource could not be found
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
      </div>
    )
  }

  return <>{children}</>
}