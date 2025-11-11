'use client'

import { useAuth } from '@/contexts/AuthContext'
import { ReactNode } from 'react'

interface AttendanceAccessControlProps {
  children: ReactNode
  requiredRole?: 'admin' | 'employee' | 'manager'
}

export function AttendanceAccessControl({ 
  children, 
  requiredRole = 'admin' 
}: AttendanceAccessControlProps) {
  const { user } = useAuth()

  // Check if user has the required role
  const hasAccess = user?.role === requiredRole

  if (!hasAccess) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Access Denied</h1>
          <p className="text-gray-600">
            You don't have permission to access this page.
          </p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}