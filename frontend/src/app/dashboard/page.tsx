'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { AdminDashboard } from '@/components/AdminDashboard'
import { EmployeeDashboard } from '@/components/EmployeeDashboard'

export default function DashboardPage() {
  const { user, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    // Handle role-based redirection
    if (!isLoading && user) {
      if (user.role === 'admin') {
        // User is admin, show admin dashboard
        // No additional action needed - AdminDashboard will be rendered below
      } else if (user.role === 'employee') {
        // User is employee, show employee dashboard
        // No additional action needed - EmployeeDashboard will be rendered below
      } else {
        // Unknown role, redirect to home
        router.push('/')
      }
    }
  }, [user, isLoading, router])

  // Handle loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  // Handle no user (shouldn't happen due to ProtectedRoute, but just in case)
  if (!user) {
    router.push('/login')
    return null
  }

  // Render appropriate dashboard based on role
  if (user.role === 'admin') {
    return <AdminDashboard />
  } else if (user.role === 'employee') {
    return <EmployeeDashboard />
  } else {
    // Unknown role, show error
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Access Denied</h1>
          <p className="text-gray-600">You don't have permission to access this dashboard.</p>
        </div>
      </div>
    )
  }
}