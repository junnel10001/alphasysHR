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
  Users,
  Clock,
  DollarSign,
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

interface OvertimeRecord {
  id: number
  employee_id: number
  employee_name: string
  date: string
  hours_worked: number
  rate_per_hour: number
  total_pay: number
  status: 'Pending' | 'Approved' | 'Rejected'
  description: string
  submitted_at: string
}

export default function OvertimePage() {
  const { user } = useAuth()
  const [overtimeRecords, setOvertimeRecords] = useState<OvertimeRecord[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchOvertimeRecords()
  }, [])

  const fetchOvertimeRecords = async () => {
    try {
      setIsLoading(true)
      // Mock data for demonstration
      const mockRecords: OvertimeRecord[] = [
        {
          id: 1,
          employee_id: 1,
          employee_name: 'John Admin',
          date: '2025-01-25',
          hours_worked: 4,
          rate_per_hour: 150,
          total_pay: 600,
          status: 'Approved',
          description: 'Project deadline work',
          submitted_at: '2025-01-24'
        },
        {
          id: 2,
          employee_id: 2,
          employee_name: 'Jane Doe',
          date: '2025-01-24',
          hours_worked: 2,
          rate_per_hour: 150,
          total_pay: 300,
          status: 'Pending',
          description: 'Client meeting preparation',
          submitted_at: '2025-01-23'
        },
        {
          id: 3,
          employee_id: 3,
          employee_name: 'Bob Smith',
          date: '2025-01-23',
          hours_worked: 3,
          rate_per_hour: 150,
          total_pay: 450,
          status: 'Rejected',
          description: 'System maintenance',
          submitted_at: '2025-01-22'
        },
        {
          id: 4,
          employee_id: 4,
          employee_name: 'Alice Johnson',
          date: '2025-01-22',
          hours_worked: 5,
          rate_per_hour: 150,
          total_pay: 750,
          status: 'Approved',
          description: 'Feature development',
          submitted_at: '2025-01-21'
        },
        {
          id: 5,
          employee_id: 5,
          employee_name: 'Mike Wilson',
          date: '2025-01-21',
          hours_worked: 1,
          rate_per_hour: 150,
          total_pay: 150,
          status: 'Pending',
          description: 'Bug fixing',
          submitted_at: '2025-01-20'
        }
      ]
      setOvertimeRecords(mockRecords)
    } catch (error) {
      console.error('Error fetching overtime records:', error)
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

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-PH', {
      style: 'currency',
      currency: 'PHP'
    }).format(amount)
  }

  const filteredRecords = overtimeRecords.filter(record =>
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
      <LayoutWrapper>
        <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Overtime</h1>
            <p className="text-muted-foreground">Manage employee overtime requests and payments</p>
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Request Overtime
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
                    placeholder="Search overtime records..."
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
              <CardTitle className="text-sm font-medium">Total Overtime</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {overtimeRecords.reduce((sum, record) => sum + record.hours_worked, 0)}h
              </div>
              <p className="text-xs text-muted-foreground">This month</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Pay</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatCurrency(overtimeRecords.reduce((sum, record) => sum + record.total_pay, 0))}
              </div>
              <p className="text-xs text-muted-foreground">This month</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Approved</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {overtimeRecords.filter(r => r.status === 'Approved').length}
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
                {overtimeRecords.filter(r => r.status === 'Pending').length}
              </div>
              <p className="text-xs text-muted-foreground">Awaiting approval</p>
            </CardContent>
          </Card>
        </div>

        {/* Overtime Table */}
        <Card>
          <CardHeader>
            <CardTitle>Overtime Requests</CardTitle>
            <CardDescription>
              Employee overtime request management and approval
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Employee</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Hours</TableHead>
                    <TableHead>Rate</TableHead>
                    <TableHead>Total Pay</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Description</TableHead>
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
                        <TableCell>{record.hours_worked}h</TableCell>
                        <TableCell>{formatCurrency(record.rate_per_hour)}/h</TableCell>
                        <TableCell className="font-semibold">{formatCurrency(record.total_pay)}</TableCell>
                        <TableCell>{getStatusBadge(record.status)}</TableCell>
                        <TableCell className="max-w-xs truncate">{record.description}</TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center py-6">
                        No overtime records found
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