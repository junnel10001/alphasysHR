'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { LayoutWrapper } from '@/components/layout'
import { ProtectedRoute } from '@/components/ProtectedRoute'
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
  Calendar,
  Clock,
  User,
  CheckCircle,
  XCircle,
  AlertCircle,
  Plus
} from 'lucide-react'
import { format } from 'date-fns'

interface LeaveRecord {
  id: number
  employee_id: number
  leave_type: string
  start_date: string
  end_date: string
  reason: string
  status: 'Pending' | 'Approved' | 'Rejected'
  created_at: string
}

export default function MyLeavePage() {
  const { user } = useAuth()
  const [leaveRecords, setLeaveRecords] = useState<LeaveRecord[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchMyLeaveRecords()
  }, [])

  const fetchMyLeaveRecords = async () => {
    try {
      setIsLoading(true)
      // Mock data for demonstration
      const mockRecords: LeaveRecord[] = [
        {
          id: 1,
          employee_id: user?.id || 1,
          leave_type: 'Vacation',
          start_date: '2025-01-15',
          end_date: '2025-01-17',
          reason: 'Family vacation',
          status: 'Approved',
          created_at: '2025-01-10'
        },
        {
          id: 2,
          employee_id: user?.id || 1,
          leave_type: 'Sick Leave',
          start_date: '2025-01-20',
          end_date: '2025-01-21',
          reason: 'Flu',
          status: 'Pending',
          created_at: '2025-01-18'
        },
        {
          id: 3,
          employee_id: user?.id || 1,
          leave_type: 'Emergency',
          start_date: '2025-01-25',
          end_date: '2025-01-25',
          reason: 'Family emergency',
          status: 'Rejected',
          created_at: '2025-01-23'
        }
      ]
      setLeaveRecords(mockRecords)
    } catch (error) {
      console.error('Error fetching leave records:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      'Approved': { label: 'Approved', color: 'bg-green-100 text-green-800', icon: CheckCircle },
      'Pending': { label: 'Pending', color: 'bg-yellow-100 text-yellow-800', icon: Clock },
      'Rejected': { label: 'Rejected', color: 'bg-red-100 text-red-800', icon: XCircle }
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

  const calculateDays = (startDate: string, endDate: string) => {
    const start = new Date(startDate)
    const end = new Date(endDate)
    const diffTime = Math.abs(end.getTime() - start.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1
    return `${diffDays} day${diffDays > 1 ? 's' : ''}`
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return (
    <ProtectedRoute>
      <LayoutWrapper>
        <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">My Leave</h1>
            <p className="text-muted-foreground">Manage your leave requests</p>
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Request Leave
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{leaveRecords.length}</div>
              <p className="text-xs text-muted-foreground">Your leave history</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Approved</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {leaveRecords.filter(r => r.status === 'Approved').length}
              </div>
              <p className="text-xs text-muted-foreground">Successfully approved</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending</CardTitle>
              <AlertCircle className="h-4 w-4 text-yellow-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {leaveRecords.filter(r => r.status === 'Pending').length}
              </div>
              <p className="text-xs text-muted-foreground">Awaiting approval</p>
            </CardContent>
          </Card>
        </div>

        {/* Leave Table */}
        <Card>
          <CardHeader>
            <CardTitle>My Leave Requests</CardTitle>
            <CardDescription>
              Your personal leave request history
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Leave Type</TableHead>
                    <TableHead>Dates</TableHead>
                    <TableHead>Days</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {leaveRecords.length > 0 ? (
                    leaveRecords.map((record) => (
                      <TableRow key={record.id}>
                        <TableCell className="font-medium">{record.leave_type}</TableCell>
                        <TableCell>
                          {formatDate(record.start_date)} - {formatDate(record.end_date)}
                        </TableCell>
                        <TableCell>{calculateDays(record.start_date, record.end_date)}</TableCell>
                        <TableCell>{getStatusBadge(record.status)}</TableCell>
                        <TableCell className="max-w-xs truncate">{record.reason}</TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-6">
                        No leave records found
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