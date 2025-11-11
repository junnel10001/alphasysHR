'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { LayoutWrapper } from '@/components/layout'
import { employeeService, departmentService, roleService } from '@/lib/api'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select'
import { ArrowLeft, Save } from 'lucide-react'

export default function EmployeeEditPage() {
  const params = useParams()
  const router = useRouter()
  const employeeId = params.employeeId as string
  const [employee, setEmployee] = useState<any>(null)
  const [departments, setDepartments] = useState<any[]>([])
  const [roles, setRoles] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Form state
  const [formData, setFormData] = useState({
    company_id: '',
    first_name: '',
    middle_name: '',
    last_name: '',
    suffix: '',
    nickname: '',
    date_of_birth: '',
    place_of_birth: '',
    gender: '',
    civil_status: '',
    nationality: '',
    blood_type: '',
    religion: '',
    mobile_number: '',
    landline_number: '',
    personal_email: '',
    current_address: '',
    permanent_address: '',
    emergency_contact_name: '',
    emergency_contact_number: '',
    emergency_contact_relationship: '',
    job_title: '',
    department_id: '',
    role_id: '',
    employment_status: '',
    date_hired: '',
    date_regularised: '',
    basic_salary: '',
    pay_frequency: '',
    bank_name: '',
    bank_account_number: '',
    payment_method: '',
  })

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true)
        
        // Fetch employee data
        const employeeData = await employeeService.getEmployee(parseInt(employeeId))
        setEmployee(employeeData)
        
        // Set form data
        setFormData({
          company_id: employeeData.company_id || '',
          first_name: employeeData.first_name || '',
          middle_name: employeeData.middle_name || '',
          last_name: employeeData.last_name || '',
          suffix: employeeData.suffix || '',
          nickname: employeeData.nickname || '',
          date_of_birth: employeeData.date_of_birth || '',
          place_of_birth: employeeData.place_of_birth || '',
          gender: employeeData.gender || '',
          civil_status: employeeData.civil_status || '',
          nationality: employeeData.nationality || '',
          blood_type: employeeData.blood_type || '',
          religion: employeeData.religion || '',
          mobile_number: employeeData.mobile_number || '',
          landline_number: employeeData.landline_number || '',
          personal_email: employeeData.personal_email || '',
          current_address: employeeData.current_address || '',
          permanent_address: employeeData.permanent_address || '',
          emergency_contact_name: employeeData.emergency_contact_name || '',
          emergency_contact_number: employeeData.emergency_contact_number || '',
          emergency_contact_relationship: employeeData.emergency_contact_relationship || '',
          job_title: employeeData.job_title || '',
          department_id: employeeData.department_id?.toString() || '',
          role_id: employeeData.role_id?.toString() || '',
          employment_status: employeeData.employment_status || '',
          date_hired: employeeData.date_hired || '',
          date_regularised: employeeData.date_regularised || '',
          basic_salary: employeeData.basic_salary?.toString() || '',
          pay_frequency: employeeData.pay_frequency || '',
          bank_name: employeeData.bank_name || '',
          bank_account_number: employeeData.bank_account_number || '',
          payment_method: employeeData.payment_method || '',
        })

        // Fetch departments and roles from database
        const [departmentsData, rolesData] = await Promise.all([
          departmentService.getDepartments(),
          roleService.getRoles()
        ])
        
        setDepartments(departmentsData)
        setRoles(rolesData)
        
      } catch (err: any) {
        console.error('Failed to fetch data', err)
        if (err.response?.status === 404) {
          setError('Employee not found')
        } else {
          setError('Failed to load employee data')
        }
      } finally {
        setIsLoading(false)
      }
    }

    if (employeeId) {
      fetchData()
    }
  }, [employeeId])

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      setIsSaving(true)
      
      // Prepare data for API
      const updateData = {
        ...formData,
        department_id: formData.department_id ? parseInt(formData.department_id) : null,
        role_id: formData.role_id ? parseInt(formData.role_id) : null,
        basic_salary: formData.basic_salary ? parseFloat(formData.basic_salary) : null,
      }
      
      await employeeService.updateEmployee(parseInt(employeeId), updateData)
      router.push(`/employees/${employeeId}`)
      
    } catch (err: any) {
      console.error('Failed to update employee', err)
      setError('Failed to update employee. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <LayoutWrapper>
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
        </div>
      </LayoutWrapper>
    )
  }

  if (error && !employee) {
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
                <p className="text-muted-foreground">{error}</p>
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
              <Link href={`/employees/${employeeId}`}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Employee
              </Link>
            </Button>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Edit Employee</h1>
              <p className="text-muted-foreground">
                {employee?.first_name} {employee?.last_name}
              </p>
            </div>
          </div>
        </div>

        {error && (
          <Card>
            <CardContent className="p-4">
              <div className="text-red-600">{error}</div>
            </CardContent>
          </Card>
        )}

        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Personal Information */}
            <Card>
              <CardHeader>
                <CardTitle>Personal Information</CardTitle>
                <CardDescription>Basic personal details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="first_name">First Name *</Label>
                    <Input
                      id="first_name"
                      value={formData.first_name}
                      onChange={(e) => handleInputChange('first_name', e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="last_name">Last Name *</Label>
                    <Input
                      id="last_name"
                      value={formData.last_name}
                      onChange={(e) => handleInputChange('last_name', e.target.value)}
                      required
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="middle_name">Middle Name</Label>
                    <Input
                      id="middle_name"
                      value={formData.middle_name}
                      onChange={(e) => handleInputChange('middle_name', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="suffix">Suffix</Label>
                    <Input
                      id="suffix"
                      value={formData.suffix}
                      onChange={(e) => handleInputChange('suffix', e.target.value)}
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="nickname">Nickname</Label>
                  <Input
                    id="nickname"
                    value={formData.nickname}
                    onChange={(e) => handleInputChange('nickname', e.target.value)}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="date_of_birth">Date of Birth</Label>
                    <Input
                      id="date_of_birth"
                      type="date"
                      value={formData.date_of_birth}
                      onChange={(e) => handleInputChange('date_of_birth', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="place_of_birth">Place of Birth</Label>
                    <Input
                      id="place_of_birth"
                      value={formData.place_of_birth}
                      onChange={(e) => handleInputChange('place_of_birth', e.target.value)}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="gender">Gender</Label>
                    <Select value={formData.gender} onValueChange={(value) => handleInputChange('gender', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select gender" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Male">Male</SelectItem>
                        <SelectItem value="Female">Female</SelectItem>
                        <SelectItem value="Other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="civil_status">Civil Status</Label>
                    <Select value={formData.civil_status} onValueChange={(value) => handleInputChange('civil_status', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select civil status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Single">Single</SelectItem>
                        <SelectItem value="Married">Married</SelectItem>
                        <SelectItem value="Widowed">Widowed</SelectItem>
                        <SelectItem value="Divorced">Divorced</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="nationality">Nationality</Label>
                    <Input
                      id="nationality"
                      value={formData.nationality}
                      onChange={(e) => handleInputChange('nationality', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="blood_type">Blood Type</Label>
                    <Input
                      id="blood_type"
                      value={formData.blood_type}
                      onChange={(e) => handleInputChange('blood_type', e.target.value)}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Contact Information */}
            <Card>
              <CardHeader>
                <CardTitle>Contact Information</CardTitle>
                <CardDescription>Contact details and addresses</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="mobile_number">Mobile Number</Label>
                    <Input
                      id="mobile_number"
                      value={formData.mobile_number}
                      onChange={(e) => handleInputChange('mobile_number', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="landline_number">Landline Number</Label>
                    <Input
                      id="landline_number"
                      value={formData.landline_number}
                      onChange={(e) => handleInputChange('landline_number', e.target.value)}
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="personal_email">Personal Email</Label>
                  <Input
                    id="personal_email"
                    type="email"
                    value={formData.personal_email}
                    onChange={(e) => handleInputChange('personal_email', e.target.value)}
                  />
                </div>

                <div>
                  <Label htmlFor="current_address">Current Address</Label>
                  <Input
                    id="current_address"
                    value={formData.current_address}
                    onChange={(e) => handleInputChange('current_address', e.target.value)}
                  />
                </div>

                <div>
                  <Label htmlFor="permanent_address">Permanent Address</Label>
                  <Input
                    id="permanent_address"
                    value={formData.permanent_address}
                    onChange={(e) => handleInputChange('permanent_address', e.target.value)}
                  />
                </div>

                <div>
                  <Label htmlFor="emergency_contact_name">Emergency Contact Name</Label>
                  <Input
                    id="emergency_contact_name"
                    value={formData.emergency_contact_name}
                    onChange={(e) => handleInputChange('emergency_contact_name', e.target.value)}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="emergency_contact_number">Emergency Contact Number</Label>
                    <Input
                      id="emergency_contact_number"
                      value={formData.emergency_contact_number}
                      onChange={(e) => handleInputChange('emergency_contact_number', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="emergency_contact_relationship">Relationship</Label>
                    <Input
                      id="emergency_contact_relationship"
                      value={formData.emergency_contact_relationship}
                      onChange={(e) => handleInputChange('emergency_contact_relationship', e.target.value)}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Employment Information */}
            <Card>
              <CardHeader>
                <CardTitle>Employment Information</CardTitle>
                <CardDescription>Job and employment details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="company_id">Company ID *</Label>
                    <Input
                      id="company_id"
                      value={formData.company_id}
                      onChange={(e) => handleInputChange('company_id', e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="job_title">Job Title</Label>
                    <Input
                      id="job_title"
                      value={formData.job_title}
                      onChange={(e) => handleInputChange('job_title', e.target.value)}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="department_id">Department</Label>
                    <Select value={formData.department_id} onValueChange={(value) => handleInputChange('department_id', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select department" />
                      </SelectTrigger>
                      <SelectContent>
                        {departments.map((dept) => (
                          <SelectItem key={dept.department_id} value={dept.department_id.toString()}>
                            {dept.department_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="role_id">Role</Label>
                    <Select value={formData.role_id} onValueChange={(value) => handleInputChange('role_id', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select role" />
                      </SelectTrigger>
                      <SelectContent>
                        {roles.map((role) => (
                          <SelectItem key={role.role_id} value={role.role_id.toString()}>
                            {role.role_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="employment_status">Employment Status</Label>
                    <Select value={formData.employment_status} onValueChange={(value) => handleInputChange('employment_status', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Regular">Regular</SelectItem>
                        <SelectItem value="Probationary">Probationary</SelectItem>
                        <SelectItem value="Contractual">Contractual</SelectItem>
                        <SelectItem value="Project-Based">Project-Based</SelectItem>
                        <SelectItem value="Part-time">Part-time</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="pay_frequency">Pay Frequency</Label>
                    <Select value={formData.pay_frequency} onValueChange={(value) => handleInputChange('pay_frequency', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select frequency" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Monthly">Monthly</SelectItem>
                        <SelectItem value="Semi-Monthly">Semi-Monthly</SelectItem>
                        <SelectItem value="Weekly">Weekly</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="date_hired">Date Hired</Label>
                    <Input
                      id="date_hired"
                      type="date"
                      value={formData.date_hired}
                      onChange={(e) => handleInputChange('date_hired', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="date_regularised">Date Regularised</Label>
                    <Input
                      id="date_regularised"
                      type="date"
                      value={formData.date_regularised}
                      onChange={(e) => handleInputChange('date_regularised', e.target.value)}
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="basic_salary">Basic Salary</Label>
                  <Input
                    id="basic_salary"
                    type="number"
                    step="0.01"
                    value={formData.basic_salary}
                    onChange={(e) => handleInputChange('basic_salary', e.target.value)}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Bank Information */}
            <Card>
              <CardHeader>
                <CardTitle>Bank Information</CardTitle>
                <CardDescription>Payment and bank details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="bank_name">Bank Name</Label>
                    <Input
                      id="bank_name"
                      value={formData.bank_name}
                      onChange={(e) => handleInputChange('bank_name', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="bank_account_number">Bank Account Number</Label>
                    <Input
                      id="bank_account_number"
                      value={formData.bank_account_number}
                      onChange={(e) => handleInputChange('bank_account_number', e.target.value)}
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="payment_method">Payment Method</Label>
                  <Select value={formData.payment_method} onValueChange={(value) => handleInputChange('payment_method', value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select payment method" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ATM">ATM</SelectItem>
                      <SelectItem value="Cash">Cash</SelectItem>
                      <SelectItem value="Cheque">Cheque</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-4 mt-6">
            <Button type="button" variant="outline" asChild>
              <Link href={`/employees/${employeeId}`}>Cancel</Link>
            </Button>
            <Button type="submit" disabled={isSaving}>
              <Save className="mr-2 h-4 w-4" />
              {isSaving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </div>
    </LayoutWrapper>
  )
}