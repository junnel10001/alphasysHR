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
  Clock,
  Calendar,
  DollarSign,
  CheckCircle,
  XCircle,
  AlertCircle,
  Plus
} from 'lucide-react'
import { format } from 'date-fns'

interface OvertimeRecord {
  id: number
  employee_id: number
  date: string
  hours_worked: number
  rate_per_hour: number
  total_pay: number
  status: 'Pending' | 'Approved' | 'Rejected'
  description: string
  submitted_at: string
}

export default function MyOvertimePage() {
  const { user } = useAuth()
  const [overtimeRecords, setOvertimeRecords] = useState<OvertimeRecord[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchMyOvertimeRecords()
  }, [])

  const fetchMyOvertimeRecords = async () => {
    try {
      setIsLoading(true)
      // Mock data for demonstration
      const mockRecords: OvertimeRecord[] = [
        {
          id: 1,
          employee_id: user?.id || 1,
          date: '2025-01-15',
          hours_worked: 4,
          rate_per_hour: 150,
          total_pay: 600,
          status: 'Approved',
          description: 'Project deadline work',
          submitted_at: '2025-01-14'
        },
        {
          id: 2,
          employee_id: user?.id || 1,
          date: '2025-01-20',
          hours_worked: 2,
          rate_per_hour: 150,
          total_pay: 300,
          status: 'Pending',
          description: 'Client meeting preparation',
          submitted_at: '2025-01-19'
        },
        {
          id: 3,
          employee_id: user?.id || 1,
          date: '2025-01-25',
          hours_worked: 3,
          rate_per_hour: 150,
          total_pay: 450,
          status: 'Rejected',
          description: 'System maintenance',
          submitted_at: '2025-01-24'
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
            <h1 className="text-3xl font-bold tracking-tight">My Overtime</h1>
            <p className="text-muted-foreground">Manage your overtime requests and payments</p>
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Request Overtime
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Hours</CardTitle>
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
            <CardTitle>My Overtime Requests</CardTitle>
            <CardDescription>
              Your personal overtime request history
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Hours</TableHead>
                    <TableHead>Rate</TableHead>
                    <TableHead>Total Pay</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Description</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {overtimeRecords.length > 0 ? (
                    overtimeRecords.map((record) => (
                      <TableRow key={record.id}>
                        <TableCell>{formatDate(record.date)}</TableCell>
                        <TableCell>{record.hours_worked}h</TableCell>
                        <TableCell>{formatCurrency(record.rate_per_hour)}/h</TableCell>
                        <TableCell className="font-semibold">{formatCurrency(record.total_pay)}</TableCell>
                        <TableCell>{getStatusBadge(record.status)}</TableCell>
                        <TableCell className="max-w-xs truncate">{record.description}</TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-6">
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