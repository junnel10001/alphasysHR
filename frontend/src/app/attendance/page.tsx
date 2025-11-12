'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { LayoutWrapper } from '@/components/layout'
import { attendanceService } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Users,
  Clock,
  Calendar,
  MoreHorizontal,
  Plus,
  Search,
  Filter,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react'
import { format } from 'date-fns'

interface AttendanceRecord {
  id: number
  employee_id: number
  employee_name: string
  date: string
  time_in: string | null
  time_out: string | null
  hours_worked: number | null
  status: 'Present' | 'Late' | 'Absent' | 'On Leave'
}

export default function AttendancePage() {
  const { user } = useAuth()
  const [attendanceRecords, setAttendanceRecords] = useState<AttendanceRecord[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchAttendanceRecords()
  }, [])

  const fetchAttendanceRecords = async () => {
    try {
      setIsLoading(true)
      const response = await attendanceService.getAttendance()
      // Transform the data to match the frontend interface
      const records = (response.data || response).map((record: any) => ({
        id: record.attendance_id,
        employee_id: record.user_id,
        employee_name: `${record.user?.first_name || ''} ${record.user?.last_name || ''}`,
        date: record.date,
        time_in: record.time_in,
        time_out: record.time_out,
        hours_worked: record.hours_worked,
        status: record.status
      }))
      setAttendanceRecords(records)
    } catch (error) {
      console.error('Error fetching attendance records:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      'Present': { label: 'Present', color: 'bg-green-100 text-green-800', icon: CheckCircle },
      'Late': { label: 'Late', color: 'bg-yellow-100 text-yellow-800', icon: AlertCircle },
      'Absent': { label: 'Absent', color: 'bg-red-100 text-red-800', icon: XCircle },
      'On Leave': { label: 'On Leave', color: 'bg-blue-100 text-blue-800', icon: Calendar }
    }
    
    const config = statusConfig[status as keyof typeof statusConfig]
    if (!config) return <Badge variant="secondary">{status}</Badge>
    
    return (
      <Badge className={config.color}>
        <config.icon className="h-3 w-3 mr-1" />
        {config.label}
      </Badge>
    )
  }

  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'MMM dd, yyyy')
  }

  const formatTime = (timeString: string | null) => {
    if (!timeString) return '--:--'
    return format(new Date(`2000-01-01T${timeString}`), 'hh:mm a')
  }

  const filteredRecords = attendanceRecords.filter(record =>
    record.employee_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    record.date.includes(searchTerm) ||
    record.status.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return (
    <ProtectedRoute requiredRole="admin">
      <LayoutWrapper requiredRole="admin">
        <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Attendance</h1>
            <p className="text-muted-foreground">Manage employee attendance records</p>
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Mark Attendance
          </Button>
        </div>

        {/* Search and Filter */}
        <Card>
          <CardHeader>
            <CardTitle>Search & Filter</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex space-x-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <input
                    type="text"
                    placeholder="Search attendance records..."
                    className="w-full pl-10 pr-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
              </div>
              <Button variant="outline">
                <Filter className="h-4 w-4 mr-2" />
                Filters
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Records</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{attendanceRecords.length}</div>
              <p className="text-xs text-muted-foreground">All records</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Present</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {attendanceRecords.filter(r => r.status === 'Present').length}
              </div>
              <p className="text-xs text-muted-foreground">On time</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Late</CardTitle>
              <AlertCircle className="h-4 w-4 text-yellow-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {attendanceRecords.filter(r => r.status === 'Late').length}
              </div>
              <p className="text-xs text-muted-foreground">Late arrivals</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Absent</CardTitle>
              <XCircle className="h-4 w-4 text-red-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {attendanceRecords.filter(r => r.status === 'Absent').length}
              </div>
              <p className="text-xs text-muted-foreground">Absent days</p>
            </CardContent>
          </Card>
        </div>

        {/* Attendance Table */}
        <Card>
          <CardHeader>
            <CardTitle>Attendance Records</CardTitle>
            <CardDescription>
              Employee attendance tracking and management
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Employee</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Time In</TableHead>
                    <TableHead>Time Out</TableHead>
                    <TableHead>Hours Worked</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRecords.length > 0 ? (
                    filteredRecords.map((record) => (
                      <TableRow key={record.id}>
                        <TableCell>
                          <div className="flex items-center space-x-3">
                            <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                              <span className="text-sm font-medium">
                                {record.employee_name.split(' ').map(n => n[0]).join('')}
                              </span>
                            </div>
                            <div>
                              <div className="font-medium">{record.employee_name}</div>
                              <div className="text-sm text-muted-foreground">ID: {record.employee_id}</div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>{formatDate(record.date)}</TableCell>
                        <TableCell>{formatTime(record.time_in)}</TableCell>
                        <TableCell>{formatTime(record.time_out)}</TableCell>
                        <TableCell>
                          {record.hours_worked ? `${record.hours_worked}h` : '--'}
                        </TableCell>
                        <TableCell>{getStatusBadge(record.status)}</TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-6">
                        No attendance records found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
        </div>
      </LayoutWrapper>
    </ProtectedRoute>
  )
}