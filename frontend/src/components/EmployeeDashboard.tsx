'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { LayoutWrapper } from '@/components/layout'
import { dashboardService } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  User,
  Clock,
  Calendar,
  DollarSign,
  FileText,
  Activity,
  LogOut,
  Settings
} from 'lucide-react'

interface DashboardData {
  employees_present: number
  late_absent: number
  pending_leave: number
  pending_overtime: number
  attendance_overview: any
  today_attendance: any
  payroll_summary: any
  leave_stats: any
  overtime_stats: any
}

export function EmployeeDashboard() {
  const { user, logout } = useAuth()
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [
          employeesPresent,
          lateAbsent,
          pendingLeave,
          pendingOvertime,
          attendanceOverview,
          todayAttendance,
          payrollSummary,
          leaveStats,
          overtimeStats
        ] = await Promise.all([
          dashboardService.getEmployeesPresent(),
          dashboardService.getLateAbsent(),
          dashboardService.getPendingLeave(),
          dashboardService.getPendingOvertime(),
          dashboardService.getAttendanceOverview(),
          dashboardService.getTodayAttendance(),
          dashboardService.getPayrollSummary(),
          dashboardService.getLeaveStats(),
          dashboardService.getOvertimeStats()
        ])

        setDashboardData({
          employees_present: employeesPresent.count,
          late_absent: lateAbsent.count,
          pending_leave: pendingLeave.count,
          pending_overtime: pendingOvertime.count,
          attendance_overview: attendanceOverview,
          today_attendance: todayAttendance,
          payroll_summary: payrollSummary,
          leave_stats: leaveStats,
          overtime_stats: overtimeStats
        })
      } catch (error) {
        console.error('Error fetching dashboard data:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchDashboardData()
    // return () => {}
  }, [])

  const navigationItems = [
    { title: 'My Profile', icon: User, href: '/profile' },
    { title: 'My Attendance', icon: Clock, href: '/my-attendance' },
    { title: 'My Leave', icon: Calendar, href: '/my-leave' },
    { title: 'My Payroll', icon: DollarSign, href: '/my-payroll' },
    { title: 'My Overtime', icon: FileText, href: '/my-overtime' },
    { title: 'Activity Logs', icon: Activity, href: '/activity' },
    { title: 'Settings', icon: Settings, href: '/settings' }
  ]

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return (
    <LayoutWrapper requiredRole="employee">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Employee Dashboard</h1>
            <p className="text-muted-foreground">Welcome back, {user?.full_name}</p>
          </div>
          <Button variant="outline" size="sm" onClick={logout}>
            <LogOut className="h-4 w-4 mr-2" />
            Logout
          </Button>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium font-kumbh-sans">Total Employees</CardTitle>
              <User className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardData?.employees_present}</div>
              <p className="text-xs text-muted-foreground">Company total</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium font-kumbh-sans">Late Today</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardData?.late_absent}</div>
              <p className="text-xs text-muted-foreground">Company total</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium font-kumbh-sans">My Leave Requests</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">2</div>
              <p className="text-xs text-muted-foreground">1 pending</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium font-kumbh-sans">My Overtime</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">1</div>
              <p className="text-xs text-muted-foreground">Pending approval</p>
            </CardContent>
          </Card>
        </div>

        {/* Navigation Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {navigationItems.map((item) => (
            <Card key={item.title} className="cursor-pointer hover:shadow-md transition-shadow">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 font-kumbh-sans">
                  <item.icon className="h-5 w-5" />
                  <span>{item.title}</span>
                </CardTitle>
                <CardDescription>
                  Access {item.title.toLowerCase()}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => window.location.href = item.href}
                >
                  Go to {item.title}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </LayoutWrapper>
  )
}