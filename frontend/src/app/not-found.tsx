'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { AlertTriangle, Home, ArrowLeft, RefreshCw } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { PublicLayout } from '@/components/layout'

export default function NotFound() {
  const router = useRouter()
  
  // Handle client-side only operations
  const handleNavigation = (action: () => void) => {
    if (typeof window !== 'undefined') {
      action()
    }
  }

  return (
    <PublicLayout
      title="Page Not Found"
      description="The page you're looking for doesn't exist or has been moved."
    >
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
          <p className="text-sm text-muted-foreground text-center">
            Error 404 - The requested resource could not be found
          </p>
          <div className="flex space-x-2 w-full">
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => handleNavigation(() => router.push('/'))}
            >
              <Home className="h-4 w-4 mr-2" />
              Go to Home
            </Button>
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => handleNavigation(() => router.back())}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Go Back
            </Button>
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => handleNavigation(() => router.refresh())}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
          <div className="mt-4 text-center">
            <p className="text-xs text-muted-foreground">
              You can also check out these popular pages:
            </p>
            <div className="flex justify-center space-x-2 mt-2">
              <Link href="/dashboard" prefetch={false}>
                <Button variant="ghost" size="sm">
                  Dashboard
                </Button>
              </Link>
              <Link href="/my-attendance" prefetch={false}>
                <Button variant="ghost" size="sm">
                  My Attendance
                </Button>
              </Link>
              <Link href="/profile" prefetch={false}>
                <Button variant="ghost" size="sm">
                  Profile
                </Button>
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>
    </PublicLayout>
  )
}