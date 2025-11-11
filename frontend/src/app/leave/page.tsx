'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { LayoutWrapper } from '@/components/layout'
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
  Calendar,
  Clock,
  MoreHorizontal,
  Plus,
  Search,
  Filter,
  CheckCircle,
  XCircle,
  AlertCircle,
  FileText
} from 'lucide-react'
import { format } from 'date-fns'

interface LeaveRecord {
  id: number
  employee_id: number
  employee_name: string
  leave_type: string
  start_date: string
  end_date: string
  total_days: number
  reason: string
  status: 'Pending' | 'Approved' | 'Rejected'
  submitted_at: string
}

export default function LeavePage() {
  const { user } = useAuth()
  const [leaveRecords, setLeaveRecords] = useState<LeaveRecord[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchLeaveRecords()
  }, [])

  const fetchLeaveRecords = async () => {
    try {
      setIsLoading(true)
      // Mock data for demonstration
      const mockRecords: LeaveRecord[] = [
        {
          id: 1,
          employee_id: 1,
          employee_name: 'John Admin',
          leave_type: 'Vacation Leave',
          start_date: '2025-02-10',
          end_date: '2025-02-14',
          total_days: 5,
          reason: 'Family vacation',
          status: 'Approved',
          submitted_at: '2025-01-20'
        },
        {
          id: 2,
          employee_id: 2,
          employee_name: 'Jane Doe',
          leave_type: 'Sick Leave',
          start_date: '2025-01-28',
          end_date: '2025-01-29',
          total_days: 2,
          reason: 'High fever',
          status: 'Pending',
          submitted_at: '2025-01-25'
        },
        {
          id: 3,
          employee_id: 3,
          employee_name: 'Bob Smith',
          leave_type: 'Emergency Leave',
          start_date: '2025-01-30',
          end_date: '2025-01-30',
          total_days: 1,
          reason: 'Family emergency',
          status: 'Rejected',
          submitted_at: '2025-01-28'
        },
        {
          id: 4,
          employee_id: 4,
          employee_name: 'Alice Johnson',
          leave_type: 'Maternity Leave',
          start_date: '2025-03-01',
          end_date: '2025-03-31',
          total_days: 31,
          reason: 'Childbirth and recovery',
          status: 'Approved',
          submitted_at: '2025-01-15'
        },
        {
          id: 5,
          employee_id: 5,
          employee_name: 'Mike Wilson',
          leave_type: 'Paternity Leave',
          start_date: '2025-02-15',
          end_date: '2025-02-20',
          total_days: 6,
          reason: 'Newborn child care',
          status: 'Pending',
          submitted_at: '2025-01-22'
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

  const filteredRecords = leaveRecords.filter(record =>
    record.employee_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    record.leave_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
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
            <h1 className="text-3xl font-bold tracking-tight">Leave Management</h1>
            <p className="text-muted-foreground">Manage employee leave requests</p>
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Request Leave
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
                    placeholder="Search leave records..."
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
              <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{leaveRecords.length}</div>
              <p className="text-xs text-muted-foreground">All requests</p>
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
              <Clock className="h-4 w-4 text-yellow-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {leaveRecords.filter(r => r.status === 'Pending').length}
              </div>
              <p className="text-xs text-muted-foreground">Awaiting approval</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Rejected</CardTitle>
              <XCircle className="h-4 w-4 text-red-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {leaveRecords.filter(r => r.status === 'Rejected').length}
              </div>
              <p className="text-xs text-muted-foreground">Denied requests</p>
            </CardContent>
          </Card>
        </div>

        {/* Leave Table */}
        <Card>
          <CardHeader>
            <CardTitle>Leave Requests</CardTitle>
            <CardDescription>
              Employee leave request management and approval
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Employee</TableHead>
                    <TableHead>Leave Type</TableHead>
                    <TableHead>Dates</TableHead>
                    <TableHead>Days</TableHead>
                    <TableHead>Reason</TableHead>
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
                        <TableCell className="capitalize">{record.leave_type}</TableCell>
                        <TableCell>
                          <div className="text-center">
                            <div>{formatDate(record.start_date)}</div>
                            <div className="text-xs text-muted-foreground">to</div>
                            <div>{formatDate(record.end_date)}</div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="text-center">
                            <div className="font-semibold">{record.total_days} days</div>
                          </div>
                        </TableCell>
                        <TableCell className="max-w-xs truncate">{record.reason}</TableCell>
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