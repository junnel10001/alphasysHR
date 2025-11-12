'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { LayoutWrapper, PermissionProtectedRoute } from '@/components'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import {
  Users,
  Search,
  UserX,
  CheckCircle,
  Eye,
  Key,
  Shield,
  UserPlus,
  AlertCircle,
  Mail,
  LogIn,
  Settings,
  ExternalLink
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"

interface User {
  user_id: number
  username: string
  full_name: string
  email: string
  role_name: string
  status: string
  date_hired: string
}

interface CurrentUser {
  user_id?: number
  role_name?: string
}

interface Role {
  role_id: number
  role_name: string
  description: string
  user_count: number
}

interface EmployeeInfo {
  employee_found: boolean
  employee_id?: number
  user_id?: number
  company_id?: string
  first_name?: string
  last_name?: string
  email?: string
  department?: {
    department_id: number
    department_name: string
  }
  role?: {
    role_id: number
    role_name: string
    description?: string
  }
  date_hired?: string
  employment_status?: string
  basic_salary?: number
  mobile_number?: string
  current_address?: string
  message?: string
}

interface UserDeactivation {
  user_id: number
  reason: string
}

interface RoleAssignment {
  user_id: number
  role_id: number
}

export default function UserManagementPage() {
  const { user } = useAuth() as { user: CurrentUser | null }
  const [users, setUsers] = useState<User[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [employees, setEmployees] = useState<EmployeeInfo[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  
  // Dialog states
  const [isDeactivationDialogOpen, setIsDeactivationDialogOpen] = useState(false)
  const [isRoleDialogOpen, setIsRoleDialogOpen] = useState(false)
  const [isEmployeeInfoDialogOpen, setIsEmployeeInfoDialogOpen] = useState(false)
  const [isPasswordResetDialogOpen, setIsPasswordResetDialogOpen] = useState(false)
  const [isLoginAsDialogOpen, setIsLoginAsDialogOpen] = useState(false)
  
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [selectedEmployee, setSelectedEmployee] = useState<EmployeeInfo | null>(null)
  const [deactivationReason, setDeactivationReason] = useState('')
  const [selectedRoleId, setSelectedRoleId] = useState<number | null>(null)
  
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchUsers()
    fetchRoles()
  }, [])

  const fetchUsers = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const { userManagementService } = await import('@/lib/api')
      const usersData = await userManagementService.listUsers()
      setUsers(usersData)
    } catch (error: any) {
      console.error('Error fetching users:', error)
      setError(error.response?.data?.detail || 'Failed to fetch users')
    } finally {
      setIsLoading(false)
    }
  }

  const fetchRoles = async () => {
    try {
      const { roleService } = await import('@/lib/api')
      const rolesData = await roleService.getRoles()
      setRoles(rolesData)
    } catch (error: any) {
      console.error('Error fetching roles:', error)
      setError(error.response?.data?.detail || 'Failed to fetch roles')
    }
  }

  const fetchEmployeeInfo = async (userId: number) => {
    try {
      const { employeeService } = await import('@/lib/api')
      const response = await employeeService.getEmployeeByUserId(userId)
      
      // Check if the response indicates no employee was found
      if (response.employee_found === false) {
        setSelectedEmployee(null) // Set to null to show "No employee record" message
      } else {
        setSelectedEmployee(response) // Set the employee data
      }
    } catch (error: any) {
      console.error('Error fetching employee info:', error)
      const errorMessage = error.response?.data?.detail || 'Failed to fetch employee information'
      
      // Check if it's a "no employee record" error and handle it gracefully
      if (errorMessage.includes('No employee profile found')) {
        setSelectedEmployee(null) // Set to null to show "No employee record" message
      } else {
        setError(errorMessage)
      }
    }
  }

  const handleDeactivate = async () => {
    if (!selectedUser || !deactivationReason.trim()) return

    setIsSubmitting(true)
    try {
      const { userManagementService } = await import('@/lib/api')
      await userManagementService.deactivateUser({
        user_id: selectedUser.user_id,
        reason: deactivationReason
      })
      
      setUsers(users.map(user => 
        user.user_id === selectedUser.user_id
          ? { ...user, status: 'inactive' }
          : user
      ))
      
      setIsDeactivationDialogOpen(false)
      setSelectedUser(null)
      setDeactivationReason('')
    } catch (error: any) {
      console.error('Error deactivating user:', error)
      setError(error.response?.data?.detail || 'Failed to deactivate user')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleActivate = async (userToActivate: User) => {
    if (!window.confirm(`Are you sure you want to activate "${userToActivate.full_name}"?`)) {
      return
    }

    try {
      const { userManagementService } = await import('@/lib/api')
      await userManagementService.activateUser(userToActivate.user_id)
      
      setUsers(users.map(user => 
        user.user_id === userToActivate.user_id
          ? { ...user, status: 'active' }
          : user
      ))
    } catch (error: any) {
      console.error('Error activating user:', error)
      setError(error.response?.data?.detail || 'Failed to activate user')
    }
  }

  const handleAssignRole = async () => {
    if (!selectedUser || !selectedRoleId) return

    setIsSubmitting(true)
    try {
      const { userManagementService } = await import('@/lib/api')
      await userManagementService.assignUserRoles({
        user_id: selectedUser.user_id,
        role_ids: [selectedRoleId] // Single role assignment
      })
      
      const updatedRole = roles.find(r => r.role_id === selectedRoleId)
      setUsers(users.map(user => 
        user.user_id === selectedUser.user_id
          ? { ...user, role_name: updatedRole?.role_name || user.role_name }
          : user
      ))
      
      setIsRoleDialogOpen(false)
      setSelectedUser(null)
      setSelectedRoleId(null)
    } catch (error: any) {
      console.error('Error assigning role:', error)
      setError(error.response?.data?.detail || 'Failed to assign role')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSendPasswordReset = async () => {
    if (!selectedUser) return

    setIsSubmitting(true)
    try {
      // Mock password reset - in real implementation, this would call an API endpoint
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      setIsPasswordResetDialogOpen(false)
      setSelectedUser(null)
      // Show success message
      alert(`Password reset email sent to ${selectedUser.email}`)
    } catch (error: any) {
      console.error('Error sending password reset:', error)
      setError('Failed to send password reset email')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleLoginAsUser = async () => {
    if (!selectedUser) return

    setIsSubmitting(true)
    try {
      // Mock login as user - in real implementation, this would create a new session
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setIsLoginAsDialogOpen(false)
      setSelectedUser(null)
      // Show success message
      alert(`Logged in as ${selectedUser.full_name}. You can now switch back to your account.`)
    } catch (error: any) {
      console.error('Error logging in as user:', error)
      setError('Failed to login as user')
    } finally {
      setIsSubmitting(false)
    }
  }

  const openDeactivationDialog = (user: User) => {
    setSelectedUser(user)
    setDeactivationReason('')
    setIsDeactivationDialogOpen(true)
  }

  const openRoleDialog = (user: User) => {
    setSelectedUser(user)
    const currentRole = roles.find(r => r.role_name === user.role_name)
    setSelectedRoleId(currentRole?.role_id || null)
    setIsRoleDialogOpen(true)
  }

  const openEmployeeInfoDialog = async (user: User) => {
    setSelectedUser(user)
    setSelectedEmployee(null) // Reset to null to show loading state initially
    await fetchEmployeeInfo(user.user_id)
    setIsEmployeeInfoDialogOpen(true)
  }

  const openPasswordResetDialog = (user: User) => {
    setSelectedUser(user)
    setIsPasswordResetDialogOpen(true)
  }

  const openLoginAsDialog = (user: User) => {
    setSelectedUser(user)
    setIsLoginAsDialogOpen(true)
  }

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                       user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
                       user.email.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = !statusFilter || statusFilter === "all" || user.status === statusFilter
    const matchesRole = !roleFilter || roleFilter === "all" || user.role_name === roleFilter
    return matchesSearch && matchesStatus && matchesRole
  })

  const getUserRoleBadgeVariant = (roleName: string) => {
    switch (roleName) {
      case 'super_admin':
        return 'destructive'
      case 'admin':
        return 'default'
      case 'manager':
        return 'secondary'
      case 'employee':
        return 'outline'
      default:
        return 'outline'
    }
  }

  const getStatusBadgeVariant = (status: string) => {
    return status === 'active' ? 'default' : 'secondary'
  }

  const canModifyUser = (targetUser: User) => {
    // Super Admins cannot modify other Super Admins
    if (user?.role_name === 'super_admin' && targetUser.role_name === 'super_admin' && targetUser.user_id !== user?.user_id) {
      return false
    }
    return true
  }

  return (
    <PermissionProtectedRoute requiredPermission="system_config">
      <LayoutWrapper>
      <div className="space-y-6">
        {/* Error Alert */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start space-x-2">
              <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
              <div>
                <h4 className="font-semibold text-red-800">Error</h4>
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">User Management</h1>
          <p className="text-muted-foreground">Comprehensive user management with role assignment, deactivation, and more</p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex items-center space-x-2">
            <Search className="h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="max-w-sm"
            />
          </div>
          <div className="flex items-center space-x-2">
            <Label htmlFor="status-filter">Status:</Label>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="All statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center space-x-2">
            <Label htmlFor="role-filter">Role:</Label>
            <Select value={roleFilter} onValueChange={setRoleFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="All roles" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roles</SelectItem>
                <SelectItem value="super_admin">Super Admin</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
                <SelectItem value="manager">Manager</SelectItem>
                <SelectItem value="employee">Employee</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Users Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Users className="h-5 w-5" />
              <span>Users ({filteredUsers.length})</span>
            </CardTitle>
            <CardDescription>Manage user accounts, roles, and access permissions</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Full Name</TableHead>
                  <TableHead>Username</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Hired Date</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredUsers.map((user) => (
                  <TableRow key={user.user_id}>
                    <TableCell className="font-semibold">{user.full_name}</TableCell>
                    <TableCell>{user.username}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <Badge variant={getUserRoleBadgeVariant(user.role_name)}>
                        {user.role_name.replace('_', ' ').toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStatusBadgeVariant(user.status)}>
                        {user.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{user.date_hired}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end space-x-1">
                        {/* View Employee Info */}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEmployeeInfoDialog(user)}
                          title="View Employee Information"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>

                        {/* Manage Role */}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openRoleDialog(user)}
                          title="Manage Role"
                          disabled={!canModifyUser(user)}
                        >
                          <Shield className="h-4 w-4" />
                        </Button>

                        {/* Send Reset Password */}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openPasswordResetDialog(user)}
                          title="Send Password Reset"
                          disabled={!canModifyUser(user)}
                        >
                          <Key className="h-4 w-4" />
                        </Button>

                        {/* Login as User */}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openLoginAsDialog(user)}
                          title="Login as User"
                          disabled={!canModifyUser(user)}
                        >
                          <LogIn className="h-4 w-4" />
                        </Button>

                        {/* Deactivate/Activate */}
                        {user.status === 'active' ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openDeactivationDialog(user)}
                            title="Deactivate User"
                            disabled={!canModifyUser(user)}
                            className="text-destructive hover:text-destructive"
                          >
                            <UserX className="h-4 w-4" />
                          </Button>
                        ) : (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleActivate(user)}
                            title="Activate User"
                            disabled={!canModifyUser(user)}
                            className="text-green-600 hover:text-green-700"
                          >
                            <CheckCircle className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Deactivation Confirmation Dialog */}
        <Dialog open={isDeactivationDialogOpen} onOpenChange={setIsDeactivationDialogOpen}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle className="flex items-center space-x-2">
                <AlertCircle className="h-5 w-5 text-destructive" />
                <span>Deactivate User Account</span>
              </DialogTitle>
              <DialogDescription>
                You are about to deactivate the account for <strong>{selectedUser?.full_name}</strong> ({selectedUser?.email}). 
                This action will prevent the user from accessing the system.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start space-x-2">
                  <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-red-800">Warning</h4>
                    <p className="text-sm text-red-700 mt-1">
                      Deactivating this user will immediately revoke their access to the system. 
                      They will not be able to log in until their account is reactivated.
                    </p>
                  </div>
                </div>
              </div>
              <div className="space-y-2">
                <div>
                  <Label htmlFor="deactivation-reason">Reason for Deactivation</Label>
                  <Textarea
                    id="deactivation-reason"
                    value={deactivationReason}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setDeactivationReason(e.target.value)}
                    placeholder="Please provide a reason for deactivating this user account..."
                    rows={3}
                  />
                </div>
                <div className="text-sm text-muted-foreground">
                  <strong>User Details:</strong>
                </div>
                <div className="bg-gray-50 p-3 rounded border text-sm">
                  <div><strong>Name:</strong> {selectedUser?.full_name}</div>
                  <div><strong>Email:</strong> {selectedUser?.email}</div>
                  <div><strong>Current Role:</strong> {selectedUser?.role_name.replace('_', ' ').toUpperCase()}</div>
                  <div><strong>Status:</strong> {selectedUser?.status}</div>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setIsDeactivationDialogOpen(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                onClick={handleDeactivate}
                disabled={isSubmitting || !deactivationReason.trim()}
                className="bg-destructive hover:bg-destructive/90"
              >
                {isSubmitting ? 'Deactivating...' : 'Deactivate User'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Role Assignment Dialog */}
        <Dialog open={isRoleDialogOpen} onOpenChange={setIsRoleDialogOpen}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle className="flex items-center space-x-2">
                <Shield className="h-5 w-5" />
                <span>Manage Role - {selectedUser?.full_name}</span>
              </DialogTitle>
              <DialogDescription>
                Assign a single role to {selectedUser?.full_name} ({selectedUser?.email})
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start space-x-2">
                  <Shield className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-blue-800">Role Assignment</h4>
                    <p className="text-sm text-blue-700 mt-1">
                      Each user can have only one role. Select the appropriate role from the options below.
                    </p>
                  </div>
                </div>
              </div>
              
              <RadioGroup value={selectedRoleId?.toString()} onValueChange={(value) => setSelectedRoleId(parseInt(value))}>
                {roles.map((role) => (
                  <div key={role.role_id} className="flex items-center space-x-2 p-3 border rounded-lg">
                    <RadioGroupItem value={role.role_id.toString()} id={`role-${role.role_id}`} />
                    <div className="flex-1">
                      <Label htmlFor={`role-${role.role_id}`} className="font-medium cursor-pointer">
                        {role.role_name.replace('_', ' ').toUpperCase()}
                      </Label>
                      <div className="text-sm text-muted-foreground">{role.description}</div>
                      <div className="text-xs text-muted-foreground">{role.user_count} users assigned</div>
                    </div>
                  </div>
                ))}
              </RadioGroup>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setIsRoleDialogOpen(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                onClick={handleAssignRole}
                disabled={isSubmitting || !selectedRoleId}
              >
                {isSubmitting ? 'Assigning...' : 'Assign Role'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Employee Information Dialog */}
        <Dialog open={isEmployeeInfoDialogOpen} onOpenChange={setIsEmployeeInfoDialogOpen}>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle className="flex items-center space-x-2">
                <Eye className="h-5 w-5" />
                <span>Employee Information - {selectedUser?.full_name}</span>
              </DialogTitle>
              <DialogDescription>
                Complete employee profile information for {selectedUser?.full_name}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4 max-h-[400px] overflow-y-auto">
              {selectedEmployee && selectedEmployee.employee_found ? (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div>
                      <Label>Employee ID</Label>
                      <div className="font-medium">{selectedEmployee.employee_id}</div>
                    </div>
                    <div>
                      <Label>Company ID</Label>
                      <div className="font-medium">{selectedEmployee.company_id}</div>
                    </div>
                    <div>
                      <Label>Full Name</Label>
                      <div className="font-medium">{selectedEmployee.first_name} {selectedEmployee.last_name}</div>
                    </div>
                    <div>
                      <Label>Email</Label>
                      <div className="font-medium">{selectedEmployee.email}</div>
                    </div>
                    <div>
                      <Label>Mobile Number</Label>
                      <div className="font-medium">{selectedEmployee.mobile_number || 'N/A'}</div>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <Label>Department</Label>
                      <div className="font-medium">{selectedEmployee.department?.department_name || 'N/A'}</div>
                    </div>
                    <div>
                      <Label>Role</Label>
                      <div className="font-medium">{selectedEmployee.role?.role_name || 'N/A'}</div>
                    </div>
                    <div>
                      <Label>Date Hired</Label>
                      <div className="font-medium">{selectedEmployee.date_hired}</div>
                    </div>
                    <div>
                      <Label>Employment Status</Label>
                      <div className="font-medium">{selectedEmployee.employment_status || 'N/A'}</div>
                    </div>
                    <div>
                      <Label>Basic Salary</Label>
                      <div className="font-medium">{selectedEmployee.basic_salary ? `$${selectedEmployee.basic_salary}` : 'N/A'}</div>
                    </div>
                  </div>
                </div>
              ) : selectedEmployee === null || (selectedEmployee && !selectedEmployee.employee_found) ? (
                <div className="text-center py-8">
                  <div className="mb-4">
                    <Eye className="h-12 w-12 text-gray-400 mx-auto" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">No Employee Record Found</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    This user account exists but hasn't been linked to an employee record yet.
                  </p>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-left">
                    <h4 className="font-medium text-blue-800 mb-2">What does this mean?</h4>
                    <ul className="text-sm text-blue-700 space-y-1">
                      <li>• The user has a login account but no employee profile</li>
                      <li>• This might be a new user awaiting employee setup</li>
                      <li>• Or the employee record may need to be created manually</li>
                    </ul>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
                  <p className="text-muted-foreground mt-2">Loading employee information...</p>
                </div>
              )}
            </div>
            <DialogFooter>
              {selectedEmployee && selectedEmployee.employee_found && (
                <Button
                  onClick={() => {
                    window.open(`/employees/${selectedEmployee.employee_id}`, '_blank')
                  }}
                  className="mr-2"
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View Full Profile
                </Button>
              )}
              <Button
                variant="outline"
                onClick={() => setIsEmployeeInfoDialogOpen(false)}
              >
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Password Reset Dialog */}
        <Dialog open={isPasswordResetDialogOpen} onOpenChange={setIsPasswordResetDialogOpen}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle className="flex items-center space-x-2">
                <Key className="h-5 w-5" />
                <span>Send Password Reset</span>
              </DialogTitle>
              <DialogDescription>
                Send a password reset email to {selectedUser?.full_name} ({selectedUser?.email})
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start space-x-2">
                  <Mail className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-blue-800">Password Reset</h4>
                    <p className="text-sm text-blue-700 mt-1">
                      An email with a password reset link will be sent to the user's email address. 
                      The link will be valid for 24 hours.
                    </p>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 p-3 rounded border text-sm">
                <div><strong>User:</strong> {selectedUser?.full_name}</div>
                <div><strong>Email:</strong> {selectedUser?.email}</div>
                <div><strong>Role:</strong> {selectedUser?.role_name.replace('_', ' ').toUpperCase()}</div>
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setIsPasswordResetDialogOpen(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                onClick={handleSendPasswordReset}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Sending...' : 'Send Reset Email'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Login as User Dialog */}
        <Dialog open={isLoginAsDialogOpen} onOpenChange={setIsLoginAsDialogOpen}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle className="flex items-center space-x-2">
                <LogIn className="h-5 w-5" />
                <span>Login as User</span>
              </DialogTitle>
              <DialogDescription>
                Simulate logging in as {selectedUser?.full_name} ({selectedUser?.email})
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                <div className="flex items-start space-x-2">
                  <LogIn className="h-5 w-5 text-orange-600 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-orange-800">Session Simulation</h4>
                    <p className="text-sm text-orange-700 mt-1">
                      This will create a new session as if you were this user. 
                      You can switch back to your original account at any time.
                    </p>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 p-3 rounded border text-sm">
                <div><strong>User:</strong> {selectedUser?.full_name}</div>
                <div><strong>Email:</strong> {selectedUser?.email}</div>
                <div><strong>Role:</strong> {selectedUser?.role_name.replace('_', ' ').toUpperCase()}</div>
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setIsLoginAsDialogOpen(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                onClick={handleLoginAsUser}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Logging in...' : 'Login as User'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
      </LayoutWrapper>
    </PermissionProtectedRoute>
  )
}
