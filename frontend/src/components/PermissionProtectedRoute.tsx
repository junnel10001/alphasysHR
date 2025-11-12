'use client'

import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { LayoutWrapper } from '@/components'

interface PermissionProtectedRouteProps {
  children: React.ReactNode
  requiredPermission?: string
}

export function PermissionProtectedRoute({ children, requiredPermission }: PermissionProtectedRouteProps) {
  const { user, isLoading } = useAuth()
  const router = useRouter()
  const [isAuthorized, setIsAuthorized] = useState(false)

  const hasRequiredPermission = (user: any, permission: string): boolean => {
    if (!user || !user.permissions) return false
    
    // Check if user has the required permission
    return user.permissions.includes(permission)
  }

  useEffect(() => {
    // Only run on client side
    if (typeof window !== 'undefined') {
      if (!isLoading) {
        if (!user) {
          // Check if there's a token in localStorage before redirecting to login
          const hasToken = localStorage.getItem('token')
          if (!hasToken) {
            router.push('/login')
            return
          } else {
            // Token exists but user is null, this might be a temporary state
            return
          }
        }
        
        if (requiredPermission && !hasRequiredPermission(user, requiredPermission)) {
          router.push('/')
          return
        }
        
        setIsAuthorized(true)
      }
    }
   // return () => {}
  }, [user, isLoading, requiredPermission, router])

  // Handle server-side rendering
  if (typeof window === 'undefined') {
    return (
      <LayoutWrapper>
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
        </div>
      </LayoutWrapper>
    )
  }

  if (isLoading) {
    return (
      <LayoutWrapper>
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
        </div>
      </LayoutWrapper>
    )
  }

  if (!isAuthorized) {
    return null
  }

  return <>{children}</>
}