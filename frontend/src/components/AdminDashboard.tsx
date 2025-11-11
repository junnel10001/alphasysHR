'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { LayoutWrapper } from '@/components/layout'
import { dashboardService } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Users,
  Clock,
  Calendar,
  DollarSign,
  FileText,
  Activity,
  LogOut,
  Settings
} from 'lucide-react'
import { BarChart, LineChart } from '@/components/charts'

interface AttendanceOverviewItem {
  name: string
  value: number
  present: number
  late: number
  absent: number
}

interface DashboardData {
  employees_present: number
  late_absent: {
    late: number
    absent: number
  }
  pending_leave: number
  pending_overtime: number
  attendance_overview: AttendanceOverviewItem[]
  today_attendance: any
  payroll_summary: any
  leave_stats: any
  overtime_stats: any
}

export function AdminDashboard() {
  const { user, logout } = useAuth()
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // New state for top‑employee statistics
  const [topAbsent, setTopAbsent] = useState<Array<{ user_id: number; full_name: string; absent_count: number }>>([])
  const [topTardy, setTopTardy] = useState<Array<{ user_id: number; full_name: string; late_count: number }>>([])
  const [topLeave, setTopLeave] = useState<Array<{ user_id: number; full_name: string; leave_count: number }>>([])

  useEffect(() => {
    // Only run on client side
    if (typeof window !== 'undefined') {
      const fetchDashboardData = async () => {
        try {
          // Fetch each piece of data individually to avoid tuple length inference issues
          const employeesPresent = await dashboardService.getEmployeesPresent();
          console.log('employeesPresent:', employeesPresent);
          const lateAbsent = await dashboardService.getLateAbsent();
          console.log('lateAbsent:', lateAbsent);
          const pendingLeave = await dashboardService.getPendingLeave();
          console.log('pendingLeave:', pendingLeave);
          const pendingOvertime = await dashboardService.getPendingOvertime();
          console.log('pendingOvertime:', pendingOvertime);
          const attendanceOverviewRaw = await dashboardService.getAttendanceOverview();
          console.log('attendanceOverviewRaw:', attendanceOverviewRaw);
          const todayAttendance = await dashboardService.getTodayAttendance();
          console.log('todayAttendance:', todayAttendance);
          const payrollSummaryRaw = await dashboardService.getPayrollSummary();
          console.log('payrollSummaryRaw:', payrollSummaryRaw);
// Debug logs for API responses
console.log('employeesPresent:', employeesPresent);
console.log('lateAbsent:', lateAbsent);
console.log('pendingLeave:', pendingLeave);
console.log('pendingOvertime:', pendingOvertime);
console.log('attendanceOverviewRaw:', attendanceOverviewRaw);
console.log('todayAttendance:', todayAttendance);
console.log('payrollSummaryRaw:', payrollSummaryRaw);
          const leaveStatsRaw = await dashboardService.getLeaveStats();
          console.log('leaveStatsRaw:', leaveStatsRaw);
          const overtimeStatsRaw = await dashboardService.getOvertimeStats();
          console.log('overtimeStatsRaw:', overtimeStatsRaw);
          // const topSickLeaveRaw = await dashboardService.getTopSickLeave();
          const topAbsentRaw = await dashboardService.getTopAbsent();
          console.log('topAbsentRaw:', topAbsentRaw);
          const topTardyRaw = await dashboardService.getTopTardy();
          console.log('topTardyRaw:', topTardyRaw);
          const topLeaveRaw = await dashboardService.getTopLeave();
          console.log('topLeaveRaw:', topLeaveRaw);

          // Set top‑employee state
          console.log('employeesPresent:', employeesPresent);
          console.log('lateAbsent:', lateAbsent);
          console.log('pendingLeave:', pendingLeave);
          console.log('pendingOvertime:', pendingOvertime);
          console.log('attendanceOverviewRaw:', attendanceOverviewRaw);
          console.log('todayAttendance:', todayAttendance);
          // setTopSickLeave(topSickLeaveRaw?.top_sick_leave ?? [])
          setTopAbsent(topAbsentRaw?.top_absent ?? [])
          setTopTardy(topTardyRaw?.top_tardy ?? [])
          setTopLeave(topLeaveRaw?.top_leave ?? [])

// Debug: log raw attendance overview data
console.log('Attendance Overview Raw:', attendanceOverviewRaw);
          // Use real data from backend without dummy seeding
          // Map attendance overview for the generic overview chart
          const attendanceOverview = Array.isArray(attendanceOverviewRaw?.attendance_overview)
            ? attendanceOverviewRaw.attendance_overview.map((item: any) => ({
                // Use the date string as the label
                name: item.date ?? '',
                // Use only the present count as the chart value
                value: Number(item.present) ?? 0,
                present: Number(item.present) ?? 0,
                late: Number(item.late) ?? 0,
                absent: Number(item.absent) ?? 0,
              }))
            : []

          // Extract nested leave_stats object from API response
          const leaveStats = leaveStatsRaw?.leave_stats
              ? {
                  pending: leaveStatsRaw.leave_stats.pending ?? 0,
                  approved: leaveStatsRaw.leave_stats.approved ?? 0,
                  rejected: leaveStatsRaw.leave_stats.rejected ?? 0,
                  cancelled: leaveStatsRaw.leave_stats.cancelled ?? 0
                }
              : { pending: 0, approved: 0, rejected: 0, cancelled: 0 }

          // Extract nested overtime_stats object from API response
          const overtimeStats = overtimeStatsRaw?.overtime_stats
              ? {
                  pending: overtimeStatsRaw.overtime_stats.pending ?? 0,
                  approved: overtimeStatsRaw.overtime_stats.approved ?? 0,
                  rejected: overtimeStatsRaw.overtime_stats.rejected ?? 0
                }
              : { pending: 0, approved: 0, rejected: 0 }

          // Extract the actual payroll summary object from the API response.
          // The backend returns { payroll_summary: { ... } }, so we need to access that nested object.
          const payrollSummary = payrollSummaryRaw?.payroll_summary
            ? {
                total_net_pay: payrollSummaryRaw.payroll_summary.total_net_pay ?? 0,
                total_basic_pay: payrollSummaryRaw.payroll_summary.total_basic_pay ?? 0,
                total_overtime_pay: payrollSummaryRaw.payroll_summary.total_overtime_pay ?? 0,
                total_deductions: payrollSummaryRaw.payroll_summary.total_deductions ?? 0
              }
            : {
                total_net_pay: 0,
                total_basic_pay: 0,
                total_overtime_pay: 0,
                total_deductions: 0
              }

          setDashboardData({
            // KPI cards
            employees_present: employeesPresent.employees_present_today ?? 0,
            // Combine late and absent counts into a single object for display
            late_absent: {
              late: lateAbsent.late ?? 0,
              absent: lateAbsent.absent ?? 0
            },
            pending_leave: pendingLeave.pending_leave_requests ?? 0,
            pending_overtime: pendingOvertime.pending_overtime_requests ?? 0,
            // Charts data
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
    } else {
      // Server side, set loading to false
      setIsLoading(false)
    }
   // return () => {}
  }, [])

  const navigationItems = [
    { title: 'Employees', icon: Users, href: '/employees' },
    { title: 'Attendance', icon: Clock, href: '/attendance' },
    { title: 'Leave Management', icon: Calendar, href: '/leave' },
    { title: 'Payroll', icon: DollarSign, href: '/payroll' },
    { title: 'Overtime', icon: FileText, href: '/overtime' },
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
    <LayoutWrapper requiredRole="admin">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
            <p className="text-muted-foreground">Welcome back, {user?.full_name}</p>
          </div>
          <Button variant="outline" size="sm" onClick={logout}>
            <LogOut className="h-4 w-4 mr-2" />
            Logout
          </Button>
        </div>


        {/* Charts Section */}
        {/* Today vs Tomorrow Comparison Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
          {/* Attendance Yesterday vs Today */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium font-kumbh-sans">
                Attendance: Yesterday vs Today
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dashboardData && dashboardData.attendance_overview && dashboardData.attendance_overview.length >= 2 && (
                <BarChart
                  data={[
                    {
                      name: 'Yesterday',
                      value:
                        dashboardData.attendance_overview[
                          dashboardData.attendance_overview.length - 2
                        ].present ?? 0
                    },
                    {
                      name: 'Today',
                      value:
                        dashboardData.attendance_overview[
                          dashboardData.attendance_overview.length - 1
                        ].present ?? 0
                    }
                  ]}
                  title=""
                  height={250}
                  colors={['#3B82F6', '#10B981']}
                  showLegend={true}
                  showGrid={true}
                />
              )}
            </CardContent>
          </Card>

          {/* Late Arrivals: Yesterday vs Today */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium font-kumbh-sans">
                Late Arrivals: Yesterday vs Today
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dashboardData && dashboardData.attendance_overview && dashboardData.attendance_overview.length >= 2 && (
                <BarChart
                  data={[
                    {
                      name: 'Yesterday',
                      value:
                        dashboardData.attendance_overview[
                          dashboardData.attendance_overview.length - 2
                        ].late ?? 0
                    },
                    {
                      name: 'Today',
                      value:
                        dashboardData.attendance_overview[
                          dashboardData.attendance_overview.length - 1
                        ].late ?? 0
                    }
                  ]}
                  title=""
                  height={250}
                  colors={['#F59E0B', '#EF4444']}
                  showLegend={true}
                  showGrid={true}
                />
              )}
            </CardContent>
          </Card>

          {/* Absents Yesterday vs Today */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium font-kumbh-sans">
                Absents Yesterday vs Today
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dashboardData && dashboardData.attendance_overview && dashboardData.attendance_overview.length >= 2 && (
                <BarChart
                  data={[
                    {
                      name: 'Yesterday',
                      value:
                        dashboardData.attendance_overview[
                          dashboardData.attendance_overview.length - 2
                        ].absent ?? 0
                    },
                    {
                      name: 'Today',
                      value:
                        dashboardData.attendance_overview[
                          dashboardData.attendance_overview.length - 1
                        ].absent ?? 0
                    }
                  ]}
                  title=""
                  height={250}
                  colors={['#EF4444', '#F59E0B']}
                  showLegend={true}
                  showGrid={true}
                />
              )}
            </CardContent>
          </Card>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Attendance Overview Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 font-kumbh-sans">
                <Activity className="h-5 w-5" />
                <span>Attendance Overview (Last 7 Days)</span>
              </CardTitle>
              <CardDescription>Attendance overview for the last 7 days</CardDescription>
            </CardHeader>
            <CardContent>
              {dashboardData?.attendance_overview && dashboardData.attendance_overview.length > 0 ? (
                <BarChart
                  data={dashboardData.attendance_overview}
                  title=""
                  height={300}
                  colors={['#3B82F6', '#10B981', '#F59E0B', '#EF4444']}
                  showLegend={true}
                  showGrid={true}
                />
              ) : (
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  No attendance data available
                </div>
              )}
            </CardContent>
          </Card>

          {/* Payroll Summary Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 font-kumbh-sans">
                <DollarSign className="h-5 w-5" />
                <span>Payroll Summary</span>
              </CardTitle>
              <CardDescription>Current month payroll breakdown</CardDescription>
            </CardHeader>
            <CardContent>
              {dashboardData?.payroll_summary ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        ₱{dashboardData?.payroll_summary?.total_net_pay?.toLocaleString() ?? 0}
                      </div>
                      <div className="text-sm text-muted-foreground">Net Pay</div>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        ₱{dashboardData?.payroll_summary?.total_basic_pay?.toLocaleString() ?? 0}
                      </div>
                      <div className="text-sm text-muted-foreground">Basic Pay</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-4 bg-amber-50 rounded-lg">
                      <div className="text-2xl font-bold text-amber-600">
                        ₱{dashboardData?.payroll_summary?.total_overtime_pay?.toLocaleString() ?? 0}
                      </div>
                      <div className="text-sm text-muted-foreground">Overtime Pay</div>
                    </div>
                    <div className="text-center p-4 bg-red-50 rounded-lg">
                      <div className="text-2xl font-bold text-red-600">
                        ₱{dashboardData?.payroll_summary?.total_deductions?.toLocaleString() ?? 0}
                      </div>
                      <div className="text-sm text-muted-foreground">Deductions</div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  No payroll data available
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Stats Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Leave Stats Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 font-kumbh-sans">
                <Calendar className="h-5 w-5" />
                <span>Leave Request Statistics</span>
              </CardTitle>
              <CardDescription>Leave request statistics for the last 30 days</CardDescription>
            </CardHeader>
            <CardContent>
              {dashboardData?.leave_stats ? (
                <BarChart
                  data={[
                    { name: 'Pending', value: dashboardData.leave_stats.pending || 0 },
                    { name: 'Approved', value: dashboardData.leave_stats.approved || 0 },
                    { name: 'Rejected', value: dashboardData.leave_stats.rejected || 0 },
                    { name: 'Cancelled', value: dashboardData.leave_stats.cancelled || 0 }
                  ]}
                  title=""
                  height={250}
                  colors={['#F59E0B', '#10B981', '#EF4444', '#6B7280']}
                  showLegend={false}
                  showGrid={true}
                />
              ) : (
                <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                  No leave data available
                </div>
              )}
            </CardContent>
          </Card>

          {/* Overtime Stats Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 font-kumbh-sans">
                <Clock className="h-5 w-5" />
                <span>Overtime Request Statistics</span>
              </CardTitle>
              <CardDescription>Overtime request statistics for the last 30 days</CardDescription>
            </CardHeader>
            <CardContent>
              {dashboardData?.overtime_stats ? (
                <BarChart
                  data={[
                    { name: 'Pending', value: dashboardData.overtime_stats.pending || 0 },
                    { name: 'Approved', value: dashboardData.overtime_stats.approved || 0 },
                    { name: 'Rejected', value: dashboardData.overtime_stats.rejected || 0 }
                  ]}
                  title=""
                  height={250}
                  colors={['#F59E0B', '#10B981', '#EF4444']}
                  showLegend={false}
                  showGrid={true}
                />
              ) : (
                <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                  No overtime data available
                </div>
              )}
            </CardContent>
          </Card>
        </div>


  {/* Top Statistics */}
  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
    {/* Top Leave */}
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium font-kumbh-sans">
          Top 10 Employees – Leave
        </CardTitle>
      </CardHeader>
      <CardContent>
        {topLeave.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-1">Name</th>
                <th className="text-right py-1">Count</th>
              </tr>
            </thead>
            <tbody>
              {topLeave.map((emp) => (
                <tr key={emp.user_id} className="border-b">
                  <td className="py-1">{emp.full_name}</td>
                  <td className="text-right py-1">{emp.leave_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="text-muted-foreground">No data available</div>
        )}
      </CardContent>
    </Card>

    {/* Top Absent */}
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium font-kumbh-sans">
          Top 10 Employees – Absent Days
        </CardTitle>
      </CardHeader>
      <CardContent>
        {topAbsent.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-1">Name</th>
                <th className="text-right py-1">Count</th>
              </tr>
            </thead>
            <tbody>
              {topAbsent.map((emp) => (
                <tr key={emp.user_id} className="border-b">
                  <td className="py-1">{emp.full_name}</td>
                  <td className="text-right py-1">{emp.absent_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="text-muted-foreground">No data available</div>
        )}
      </CardContent>
    </Card>

    {/* Top Tardy */}
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium font-kumbh-sans">
          Top 10 Employees – Late Arrivals
        </CardTitle>
      </CardHeader>
      <CardContent>
        {topTardy.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-1">Name</th>
                <th className="text-right py-1">Count</th>
              </tr>
            </thead>
            <tbody>
              {topTardy.map((emp) => (
                <tr key={emp.user_id} className="border-b">
                  <td className="py-1">{emp.full_name}</td>
                  <td className="text-right py-1">{emp.late_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="text-muted-foreground">No data available</div>
        )}
      </CardContent>
    </Card>
  </div>
</div>
    </LayoutWrapper>
  )
}