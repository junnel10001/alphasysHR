'use client'

import { AdminDashboard } from '@/components/AdminDashboard'
import { EmployeeDashboard } from '@/components/EmployeeDashboard'
import { useAuth } from '@/contexts/AuthContext'

export default function DashboardPage() {
  const { user } = useAuth()

  // Render appropriate dashboard based on role
  // Only admin and super_admin get AdminDashboard, all others get EmployeeDashboard
  if (user?.role === 'admin' || user?.role === 'super_admin') {
    return <AdminDashboard />
  } else if (user?.role) {
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