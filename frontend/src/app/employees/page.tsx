'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { LayoutWrapper } from '@/components/layout'
import { employeeService, departmentService, roleService, invitationService } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { InvitationDialog } from '@/components/invitations/InvitationDialog'
import { InvitationStatusBadge } from '@/components/invitations/InvitationStatusBadge'
import { Invitation } from '@/types/invitation'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
} from '@/components/ui/card'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui/table'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Search, MoreHorizontal, Eye, Edit, Trash2, Mail, RefreshCw } from 'lucide-react'
import { toast } from 'react-hot-toast'

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<any[]>([])
  const [filtered, setFiltered] = useState<any[]>([])
  const [search, setSearch] = useState('')
  const [departmentFilter, setDepartmentFilter] = useState<string>('all')
  const [roleFilter, setRoleFilter] = useState<string>('all')
  const [departments, setDepartments] = useState<any[]>([])
  const [roles, setRoles] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [deleteLoading, setDeleteLoading] = useState<number | null>(null)
  const [invitationDialogOpen, setInvitationDialogOpen] = useState(false)
  const [selectedEmployee, setSelectedEmployee] = useState<any>(null)
  const [invitations, setInvitations] = useState<Invitation[]>([])

  // Load employees on mount
  useEffect(() => {
    const fetchEmployees = async () => {
      try {
        setIsLoading(true)
        // employeeService provides getEmployees()
        const data = await employeeService.getEmployees()
        setEmployees(data)
        setFiltered(data)
      } catch (err) {
        console.error('Failed to fetch employees', err)
      } finally {
        setIsLoading(false)
      }
    }
    fetchEmployees()
  }, [])

  // Load departments and roles for filters
  useEffect(() => {
    const fetchFilters = async () => {
      try {
        const [departmentsData, rolesData] = await Promise.all([
          departmentService.getDepartments(),
          roleService.getRoles()
        ])
        setDepartments(departmentsData)
        setRoles(rolesData)
      } catch (err) {
        console.error('Failed to fetch filter data', err)
      }
    }
    fetchFilters()
    
    // Load invitations to check employee invitation status
    const fetchInvitations = async () => {
      try {
        const invitationsData = await invitationService.getInvitations()
        setInvitations(invitationsData.invitations || [])
      } catch (err) {
        console.error('Failed to fetch invitations', err)
      }
    }
    fetchInvitations()
  }, [])

  // Debug invitation dialog state
  useEffect(() => {
    console.log('invitationDialogOpen state changed to:', invitationDialogOpen)
  }, [invitationDialogOpen])

  // Handle delete employee
  const handleDelete = async (employeeId: number) => {
    if (!confirm('Are you sure you want to delete this employee?')) {
      return
    }

    try {
      setDeleteLoading(employeeId)
      await employeeService.deleteEmployee(employeeId)
      // Remove from local state
      setEmployees(prev => prev.filter(emp => emp.employee_id !== employeeId))
      setFiltered(prev => prev.filter(emp => emp.employee_id !== employeeId))
    } catch (err) {
      console.error('Failed to delete employee', err)
      alert('Failed to delete employee. Please try again.')
    } finally {
      setDeleteLoading(null)
    }
  }

  // Apply filters whenever search or dropdowns change
  useEffect(() => {
    let result = employees

    if (search) {
      const lower = search.toLowerCase()
      result = result.filter(
        (e) =>
          `${e.first_name} ${e.last_name}`.toLowerCase().includes(lower) ||
          e.employee_id?.toString().includes(lower) ||
          e.personal_email?.toLowerCase().includes(lower)
      )
    }

    if (departmentFilter !== 'all') {
      result = result.filter(
        (e) => e.department?.department_id?.toString() === departmentFilter
      )
    }

    if (roleFilter !== 'all') {
      result = result.filter((e) => e.role?.role_id?.toString() === roleFilter)
    }

    setFiltered(result)
  }, [search, departmentFilter, roleFilter, employees, invitations])

  const handleInviteEmployee = (employee: any) => {
    console.log('handleInviteEmployee called with employee:', employee)
    setSelectedEmployee(employee)
    console.log('Setting invitationDialogOpen to true')
    setInvitationDialogOpen(true)
    console.log('invitationDialogOpen should now be true')
  }

  const handleInvitationSuccess = (invitation: Invitation) => {
    setInvitations(prev => [invitation, ...prev])
    setInvitationDialogOpen(false)
    setSelectedEmployee(null)
  }

  const getEmployeeInvitationStatus = (employee: any) => {
    const invitation = invitations.find(inv =>
      inv.employee_profile_id === employee.employee_id ||
      inv.email === employee.personal_email
    )
    return invitation?.status
  }

  const hasUserAccount = (employee: any) => {
    return getEmployeeInvitationStatus(employee) === 'accepted'
  }

  const canInvite = (employee: any) => {
    const status = getEmployeeInvitationStatus(employee)
    return !status || status === 'expired' || status === 'revoked'
  }

  const canResend = (employee: any) => {
    const status = getEmployeeInvitationStatus(employee)
    return status === 'pending' || status === 'expired'
  }

  const handleResendInvitation = async (employee: any) => {
    try {
      const invitation = invitations.find(inv =>
        inv.employee_profile_id === employee.employee_id ||
        inv.email === employee.personal_email
      )
      
      if (!invitation) {
        toast.error('No invitation found for this employee')
        return
      }

      await invitationService.resendInvitation({
        invitation_id: invitation.invitation_id,
        expires_days: 7
      })
      
      toast.success('Invitation resent successfully!')
      
      // Refresh invitations to get updated data
      const invitationsData = await invitationService.getInvitations()
      setInvitations(invitationsData.invitations || [])
    } catch (error: any) {
      console.error('Failed to resend invitation:', error)
      const errorMessage = error.response?.data?.detail || 'Failed to resend invitation'
      toast.error(errorMessage)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return (
    <LayoutWrapper>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Employees</h1>
          <p className="text-muted-foreground">
            Manage employee records, view details, and add new staff.
          </p>
        </div>

        {/* Filter Bar */}
        <Card className="p-4 flex flex-col md:flex-row items-center gap-4">
          <div className="flex items-center w-full md:w-auto">
            <Search className="h-4 w-4 mr-2 text-muted-foreground" />
            <Input
              placeholder="Search by name, ID, or email"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <Select value={departmentFilter} onValueChange={setDepartmentFilter}>
            <SelectTrigger className="w-full md:w-[180px]">
              <SelectValue placeholder="All Departments" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Departments</SelectItem>
              {departments.map((dept) => (
                <SelectItem key={dept.department_id} value={dept.department_id.toString()}>
                  {dept.department_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={roleFilter} onValueChange={setRoleFilter}>
            <SelectTrigger className="w-full md:w-[180px]">
              <SelectValue placeholder="All Roles" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Roles</SelectItem>
              {roles.map((role) => (
                <SelectItem key={role.role_id} value={role.role_id.toString()}>
                  {role.role_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button asChild className="ml-auto md:ml-0">
            <Link href="/employees/new">Add New Employee</Link>
          </Button>
        </Card>

        {/* Employees Table */}
        <Card>
          <CardHeader>
            <CardTitle>Employee List</CardTitle>
            <CardDescription>
              {filtered.length} employee{filtered.length !== 1 ? 's' : ''} found
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Employee ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Department</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Invitation Status</TableHead>
                    <TableHead>Date Hired</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.length > 0 ? (
                    filtered.map((emp) => (
                      <TableRow key={emp.employee_id}>
                        <TableCell>{emp.employee_id}</TableCell>
                        <TableCell>
                          {emp.first_name} {emp.last_name}
                        </TableCell>
                        <TableCell>{emp.department?.department_name ?? '-'}</TableCell>
                        <TableCell>{emp.role?.role_name ?? '-'}</TableCell>
                        <TableCell>{emp.employment_status ?? '-'}</TableCell>
                        <TableCell>
                          {getEmployeeInvitationStatus(emp) ? (
                            <InvitationStatusBadge status={getEmployeeInvitationStatus(emp) as any} />
                          ) : hasUserAccount(emp) ? (
                            <span className="text-sm text-green-600">Has Account</span>
                          ) : (
                            <span className="text-sm text-muted-foreground">No Invitation</span>
                          )}
                        </TableCell>
                        <TableCell>{emp.date_hired?.split('T')[0] ?? '-'}</TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" className="h-8 w-8 p-0">
                                <span className="sr-only">Open menu</span>
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem asChild>
                                <Link href={`/employees/${emp.employee_id}`} className="flex items-center">
                                  <Eye className="mr-2 h-4 w-4" />
                                  View
                                </Link>
                              </DropdownMenuItem>
                              <DropdownMenuItem asChild>
                                <Link href={`/employees/${emp.employee_id}/edit`} className="flex items-center">
                                  <Edit className="mr-2 h-4 w-4" />
                                  Edit
                                </Link>
                              </DropdownMenuItem>
                              {canInvite(emp) && (
                                <DropdownMenuItem
                                  onClick={() => {
                                    console.log('DropdownMenuItem onClick triggered for employee:', emp)
                                    handleInviteEmployee(emp)
                                  }}
                                  className="text-blue-600"
                                >
                                  <Mail className="mr-2 h-4 w-4" />
                                  Send Invitation
                                </DropdownMenuItem>
                              )}
                              {canResend(emp) && (
                                <DropdownMenuItem
                                  onClick={() => handleResendInvitation(emp)}
                                  className="text-orange-600"
                                >
                                  <RefreshCw className="mr-2 h-4 w-4" />
                                  Resend Invitation
                                </DropdownMenuItem>
                              )}
                              <DropdownMenuItem
                                onClick={() => handleDelete(emp.employee_id)}
                                disabled={deleteLoading === emp.employee_id}
                                className="text-red-600"
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                {deleteLoading === emp.employee_id ? 'Deleting...' : 'Delete'}
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center py-6">
                        No employees found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Invitation Dialog */}
        <InvitationDialog
          open={invitationDialogOpen}
          onOpenChange={setInvitationDialogOpen}
          onSuccess={handleInvitationSuccess}
          employeeId={selectedEmployee?.employee_id}
          defaultEmail={selectedEmployee?.personal_email}
          employee={selectedEmployee}
        />
      </div>
    </LayoutWrapper>
  )
}
