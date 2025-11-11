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
  DollarSign,
  Calendar,
  Download,
  Eye,
  FileText
} from 'lucide-react'
import { format } from 'date-fns'

interface PayrollRecord {
  id: number
  employee_id: number
  pay_period: string
  basic_salary: number
  overtime_pay: number
  deductions: number
  net_salary: number
  status: 'Processed' | 'Pending' | 'Failed'
  pay_date: string
  payslip_url?: string
}

export default function MyPayrollPage() {
  const { user } = useAuth()
  const [payrollRecords, setPayrollRecords] = useState<PayrollRecord[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchMyPayrollRecords()
  }, [])

  const fetchMyPayrollRecords = async () => {
    try {
      setIsLoading(true)
      // Mock data for demonstration
      const mockRecords: PayrollRecord[] = [
        {
          id: 1,
          employee_id: user?.id || 1,
          pay_period: 'January 2025',
          basic_salary: 25000,
          overtime_pay: 3000,
          deductions: 2000,
          net_salary: 26000,
          status: 'Processed',
          pay_date: '2025-01-31',
          payslip_url: '/payslip/1'
        },
        {
          id: 2,
          employee_id: user?.id || 1,
          pay_period: 'December 2024',
          basic_salary: 25000,
          overtime_pay: 1500,
          deductions: 1800,
          net_salary: 24700,
          status: 'Processed',
          pay_date: '2024-12-31',
          payslip_url: '/payslip/2'
        },
        {
          id: 3,
          employee_id: user?.id || 1,
          pay_period: 'February 2025',
          basic_salary: 25000,
          overtime_pay: 0,
          deductions: 2200,
          net_salary: 22800,
          status: 'Pending',
          pay_date: '2025-02-28'
        }
      ]
      setPayrollRecords(mockRecords)
    } catch (error) {
      console.error('Error fetching payroll records:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      'Processed': { label: 'Processed', color: 'bg-green-100 text-green-800', icon: DollarSign },
      'Pending': { label: 'Pending', color: 'bg-yellow-100 text-yellow-800', icon: Calendar },
      'Failed': { label: 'Failed', color: 'bg-red-100 text-red-800', icon: FileText }
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

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-PH', {
      style: 'currency',
      currency: 'PHP'
    }).format(amount)
  }

  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'MMM dd, yyyy')
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
            <h1 className="text-3xl font-bold tracking-tight">My Payroll</h1>
            <p className="text-muted-foreground">View your salary and payment information</p>
          </div>
          <Button>
            <Download className="h-4 w-4 mr-2" />
            Download Payslip
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Current Month</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(payrollRecords[0]?.net_salary || 0)}</div>
              <p className="text-xs text-muted-foreground">Net salary</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Overtime Pay</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(payrollRecords[0]?.overtime_pay || 0)}</div>
              <p className="text-xs text-muted-foreground">This month</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Deductions</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(payrollRecords[0]?.deductions || 0)}</div>
              <p className="text-xs text-muted-foreground">This month</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {payrollRecords.filter(r => r.status === 'Pending').length}
              </div>
              <p className="text-xs text-muted-foreground">Awaiting processing</p>
            </CardContent>
          </Card>
        </div>

        {/* Payroll Table */}
        <Card>
          <CardHeader>
            <CardTitle>My Payroll History</CardTitle>
            <CardDescription>
              Your salary payment history and payslips
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Pay Period</TableHead>
                    <TableHead>Basic Salary</TableHead>
                    <TableHead>Overtime</TableHead>
                    <TableHead>Deductions</TableHead>
                    <TableHead>Net Salary</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {payrollRecords.length > 0 ? (
                    payrollRecords.map((record) => (
                      <TableRow key={record.id}>
                        <TableCell className="font-medium">{record.pay_period}</TableCell>
                        <TableCell>{formatCurrency(record.basic_salary)}</TableCell>
                        <TableCell>{formatCurrency(record.overtime_pay)}</TableCell>
                        <TableCell>{formatCurrency(record.deductions)}</TableCell>
                        <TableCell className="font-semibold">{formatCurrency(record.net_salary)}</TableCell>
                        <TableCell>{getStatusBadge(record.status)}</TableCell>
                        <TableCell>
                          <Button variant="outline" size="sm">
                            <Eye className="h-4 w-4 mr-1" />
                            View
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-6">
                        No payroll records found
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