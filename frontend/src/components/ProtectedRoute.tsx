'use client'

import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredRole?: string
}

// Role hierarchy for hierarchical permission checking
const ROLE_HIERARCHY: { [key: string]: number } = {
  'super_admin': 5,  // Highest level
  'admin': 4,
  'manager': 3,
  'employee': 2,
  'guest': 1
}

export function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const { user, isLoading } = useAuth()
  const router = useRouter()
  const [isAuthorized, setIsAuthorized] = useState(false)
  const [isClient, setIsClient] = useState(false)

  const hasRequiredRole = (userRole: string, requiredRole: string): boolean => {
    if (!requiredRole) return true // No role requirement means access is granted
    
    // Check if user role matches exactly
    if (userRole === requiredRole) return true
    
    // Check hierarchy - higher number means higher privilege
    const userLevel = ROLE_HIERARCHY[userRole] || 0
    const requiredLevel = ROLE_HIERARCHY[requiredRole] || 0
    
    // User has access if their level is >= required level
    return userLevel >= requiredLevel
  }

  useEffect(() => {
    setIsClient(true)
    
    // Only run on client side
    if (!isLoading) {
      if (!user) {
        // Check if there's a token in localStorage before redirecting to login
        const hasToken = localStorage.getItem('token')
        if (!hasToken) {
          router.push('/login')
          return
        } else {
          // Token exists but user is null, this might be a temporary state
          // Try to refresh the user state
          return
        }
      }
      
      if (requiredRole && !hasRequiredRole(user.role, requiredRole)) {
        router.push('/')
        return
      }
      
      setIsAuthorized(true)
    }
   // return () => {}
  }, [user, isLoading, requiredRole, router])

  // Show loading spinner during initial load (both server and client)
  // This ensures consistent rendering between server and client
  if (isLoading || !isClient) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  if (!isAuthorized) {
    return null
  }

  return <>{children}</>
}