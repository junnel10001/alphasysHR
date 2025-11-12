'use client'

import { AdminDashboard } from '@/components/AdminDashboard'
import { EmployeeDashboard } from '@/components/EmployeeDashboard'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { useAuth } from '@/contexts/AuthContext'

export default function HomePage() {
  const { user, isLoading } = useAuth()

  // Handle loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return (
    <ProtectedRoute>
      {(() => {
        // Render appropriate dashboard based on role
        // Only admin and super_admin get AdminDashboard, all others get EmployeeDashboard
        if (user?.role === 'admin' || user?.role === 'super_admin') {
          return <AdminDashboard />
        } else if (user?.role) {
          // All other authenticated roles (employee, manager, etc.) get EmployeeDashboard
          return <EmployeeDashboard />
        } else {
          // This should not happen with ProtectedRoute, but just in case
          return (
            <div className="min-h-screen flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-2xl font-bold text-red-600 mb-4">Access Denied</h1>
                <p className="text-gray-600">You don't have permission to access this dashboard.</p>
              </div>
            </div>
          )
        }
      })()}
    </ProtectedRoute>
  )
}