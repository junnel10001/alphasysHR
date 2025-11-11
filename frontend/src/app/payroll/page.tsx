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
  DollarSign, 
  Calendar, 
  MoreHorizontal,
  Plus,
  Search,
  Filter,
  Download,
  Eye,
  FileText
} from 'lucide-react'
import { format } from 'date-fns'

interface PayrollRecord {
  id: number
  employee_id: number
  employee_name: string
  pay_period: string
  basic_salary: number
  overtime_pay: number
  allowances: number
  deductions: number
  net_salary: number
  status: 'Processed' | 'Pending' | 'Failed'
  pay_date: string
  payslip_url?: string
}

export default function PayrollPage() {
  const { user } = useAuth()
  const [payrollRecords, setPayrollRecords] = useState<PayrollRecord[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchPayrollRecords()
  }, [])

  const fetchPayrollRecords = async () => {
    try {
      setIsLoading(true)
      // Mock data for demonstration
      const mockRecords: PayrollRecord[] = [
        {
          id: 1,
          employee_id: 1,
          employee_name: 'John Admin',
          pay_period: 'January 2025',
          basic_salary: 35000,
          overtime_pay: 5000,
          allowances: 2000,
          deductions: 3000,
          net_salary: 39000,
          status: 'Processed',
          pay_date: '2025-01-31',
          payslip_url: '/payslip/1'
        },
        {
          id: 2,
          employee_id: 2,
          employee_name: 'Jane Doe',
          pay_period: 'January 2025',
          basic_salary: 32000,
          overtime_pay: 3000,
          allowances: 1500,
          deductions: 2500,
          net_salary: 34000,
          status: 'Processed',
          pay_date: '2025-01-31',
          payslip_url: '/payslip/2'
        },
        {
          id: 3,
          employee_id: 3,
          employee_name: 'Bob Smith',
          pay_period: 'January 2025',
          basic_salary: 28000,
          overtime_pay: 2000,
          allowances: 1000,
          deductions: 2000,
          net_salary: 29000,
          status: 'Pending',
          pay_date: '2025-02-28'
        },
        {
          id: 4,
          employee_id: 4,
          employee_name: 'Alice Johnson',
          pay_period: 'December 2024',
          basic_salary: 30000,
          overtime_pay: 4000,
          allowances: 1800,
          deductions: 2800,
          net_salary: 33000,
          status: 'Processed',
          pay_date: '2024-12-31',
          payslip_url: '/payslip/3'
        },
        {
          id: 5,
          employee_id: 5,
          employee_name: 'Mike Wilson',
          pay_period: 'February 2025',
          basic_salary: 26000,
          overtime_pay: 1500,
          allowances: 1200,
          deductions: 2300,
          net_salary: 26400,
          status: 'Failed',
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
      'Processed': { label: 'Processed', color: 'bg-green-100 text-green-800', icon: FileText },
      'Pending': { label: 'Pending', color: 'bg-yellow-100 text-yellow-800', icon: Calendar },
      'Failed': { label: 'Failed', color: 'bg-red-100 text-red-800', icon: DollarSign }
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

  const filteredRecords = payrollRecords.filter(record =>
    record.employee_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    record.pay_period.toLowerCase().includes(searchTerm.toLowerCase()) ||
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
            <h1 className="text-3xl font-bold tracking-tight">Payroll</h1>
            <p className="text-muted-foreground">Manage employee payroll and payments</p>
          </div>
          <div className="flex space-x-2">
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export Report
            </Button>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Process Payroll
            </Button>
          </div>
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
                    placeholder="Search payroll records..."
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
              <CardTitle className="text-sm font-medium">Total Payroll</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatCurrency(payrollRecords.reduce((sum, record) => sum + record.net_salary, 0))}
              </div>
              <p className="text-xs text-muted-foreground">This month</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Processed</CardTitle>
              <FileText className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {payrollRecords.filter(r => r.status === 'Processed').length}
              </div>
              <p className="text-xs text-muted-foreground">Successfully processed</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending</CardTitle>
              <Calendar className="h-4 w-4 text-yellow-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {payrollRecords.filter(r => r.status === 'Pending').length}
              </div>
              <p className="text-xs text-muted-foreground">Awaiting processing</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Employees</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{payrollRecords.length}</div>
              <p className="text-xs text-muted-foreground">Total employees</p>
            </CardContent>
          </Card>
        </div>

        {/* Payroll Table */}
        <Card>
          <CardHeader>
            <CardTitle>Payroll Records</CardTitle>
            <CardDescription>
              Employee payroll payment history and management
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Employee</TableHead>
                    <TableHead>Pay Period</TableHead>
                    <TableHead>Basic Salary</TableHead>
                    <TableHead>Overtime</TableHead>
                    <TableHead>Allowances</TableHead>
                    <TableHead>Deductions</TableHead>
                    <TableHead>Net Salary</TableHead>
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
                        <TableCell className="capitalize">{record.pay_period}</TableCell>
                        <TableCell>{formatCurrency(record.basic_salary)}</TableCell>
                        <TableCell>{formatCurrency(record.overtime_pay)}</TableCell>
                        <TableCell>{formatCurrency(record.allowances)}</TableCell>
                        <TableCell>{formatCurrency(record.deductions)}</TableCell>
                        <TableCell className="font-semibold">{formatCurrency(record.net_salary)}</TableCell>
                        <TableCell>{getStatusBadge(record.status)}</TableCell>
                        <TableCell>
                          <div className="flex space-x-1">
                            <Button variant="ghost" size="sm">
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="sm">
                              <Download className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-6">
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