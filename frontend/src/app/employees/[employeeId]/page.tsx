'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { LayoutWrapper } from '@/components/layout'
import { employeeService } from '@/lib/api'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ArrowLeft, Edit, Mail, Phone, Calendar, MapPin, User } from 'lucide-react'

export default function EmployeeViewPage() {
  const params = useParams()
  const router = useRouter()
  const employeeId = params.employeeId as string
  const [employee, setEmployee] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchEmployee = async () => {
      try {
        setIsLoading(true)
        const data = await employeeService.getEmployee(parseInt(employeeId))
        setEmployee(data)
      } catch (err: any) {
        console.error('Failed to fetch employee', err)
        if (err.response?.status === 404) {
          setError('Employee not found')
        } else {
          setError('Failed to load employee details')
        }
      } finally {
        setIsLoading(false)
      }
    }

    if (employeeId) {
      fetchEmployee()
    }
  }, [employeeId])

  if (isLoading) {
    return (
      <LayoutWrapper>
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
        </div>
      </LayoutWrapper>
    )
  }

  if (error || !employee) {
    return (
      <LayoutWrapper>
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/employees">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Employees
              </Link>
            </Button>
          </div>
          <Card>
            <CardContent className="p-6">
              <div className="text-center">
                <h2 className="text-2xl font-semibold text-red-600 mb-2">Error</h2>
                <p className="text-muted-foreground">{error || 'Employee not found'}</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </LayoutWrapper>
    )
  }

  return (
    <LayoutWrapper>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/employees">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Employees
              </Link>
            </Button>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                {employee.first_name} {employee.last_name}
              </h1>
              <p className="text-muted-foreground">
                Employee ID: {employee.employee_id}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" asChild>
              <Link href={`/employees/${employee.employee_id}/edit`}>
                <Edit className="mr-2 h-4 w-4" />
                Edit Employee
              </Link>
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Personal Information */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Personal Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Full Name</label>
                  <p className="font-medium">
                    {employee.first_name} {employee.middle_name} {employee.last_name} {employee.suffix}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Nickname</label>
                  <p className="font-medium">{employee.nickname || '-'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Date of Birth</label>
                  <p className="font-medium">{employee.date_of_birth || '-'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Place of Birth</label>
                  <p className="font-medium">{employee.place_of_birth || '-'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Gender</label>
                  <p className="font-medium">{employee.gender || '-'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Civil Status</label>
                  <p className="font-medium">{employee.civil_status || '-'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Nationality</label>
                  <p className="font-medium">{employee.nationality || '-'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Blood Type</label>
                  <p className="font-medium">{employee.blood_type || '-'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Religion</label>
                  <p className="font-medium">{employee.religion || '-'}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Contact Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Phone className="h-5 w-5" />
                Contact Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-muted-foreground">Mobile Number</label>
                <p className="font-medium">{employee.mobile_number || '-'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Landline Number</label>
                <p className="font-medium">{employee.landline_number || '-'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                  <Mail className="h-4 w-4" />
                  Personal Email
                </label>
                <p className="font-medium">{employee.personal_email || '-'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Current Address</label>
                <p className="font-medium text-sm">{employee.current_address || '-'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Permanent Address</label>
                <p className="font-medium text-sm">{employee.permanent_address || '-'}</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Employment Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Employment Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium text-muted-foreground">Employee ID</label>
                <p className="font-medium">{employee.employee_id}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Company ID</label>
                <p className="font-medium">{employee.company_id}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Job Title</label>
                <p className="font-medium">{employee.job_title || '-'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Department</label>
                <p className="font-medium">{employee.department?.department_name || '-'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Role</label>
                <p className="font-medium">{employee.role?.role_name || '-'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Employment Status</label>
                <Badge variant="secondary">{employee.employment_status || '-'}</Badge>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Date Hired</label>
                <p className="font-medium">{employee.date_hired?.split('T')[0] || '-'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Date Regularised</label>
                <p className="font-medium">{employee.date_regularised?.split('T')[0] || '-'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Basic Salary</label>
                <p className="font-medium">{employee.basic_salary ? `₱${employee.basic_salary.toLocaleString()}` : '-'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Pay Frequency</label>
                <p className="font-medium">{employee.pay_frequency || '-'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Bank Name</label>
                <p className="font-medium">{employee.bank_name || '-'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Bank Account Number</label>
                <p className="font-medium">{employee.bank_account_number || '-'}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Emergency Contact */}
        <Card>
          <CardHeader>
            <CardTitle>Emergency Contact</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium text-muted-foreground">Contact Name</label>
                <p className="font-medium">{employee.emergency_contact_name || '-'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Contact Number</label>
                <p className="font-medium">{employee.emergency_contact_number || '-'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Relationship</label>
                <p className="font-medium">{employee.emergency_contact_relationship || '-'}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </LayoutWrapper>
  )
}