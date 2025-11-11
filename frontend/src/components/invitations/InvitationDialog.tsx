'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Loader2, Mail, X } from 'lucide-react'
import { departmentService, roleService, invitationService } from '@/lib/api'
import { Invitation } from '@/types/invitation'

interface InvitationDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess: (invitation: Invitation) => void
  employeeId?: number
  defaultEmail?: string
  employee?: any  // Add selected employee for pre-population
}

export function InvitationDialog({
  open,
  onOpenChange,
  onSuccess,
  employeeId,
  defaultEmail = '',
  employee
}: InvitationDialogProps) {
  console.log('InvitationDialog received props:', { open, employeeId, defaultEmail })
  const [email, setEmail] = useState(defaultEmail)
  const [departmentId, setDepartmentId] = useState<string>('')
  const [roleId, setRoleId] = useState<string>('')
  const [expiresDays, setExpiresDays] = useState<string>('7')
  const [departments, setDepartments] = useState<any[]>([])
  const [roles, setRoles] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isInitialLoading, setIsInitialLoading] = useState(true)

  // Load departments and roles when dialog opens and pre-populate employee data
  useEffect(() => {
    if (open && employeeId) {
      const loadData = async () => {
        try {
          console.log('Loading departments and roles...')
          setIsInitialLoading(true)
          const [departmentsData, rolesData] = await Promise.all([
            departmentService.getDepartments(),
            roleService.getRoles()
          ])
          console.log('Departments loaded:', departmentsData)
          console.log('Roles loaded:', rolesData)
          setDepartments(departmentsData)
          setRoles(rolesData)
          
          // Pre-populate department, role, and email if employee data is available
          if (employee) {
            console.log('Pre-populating department, role, and email from employee data:', employee)
            
            // Set email from employee's personal_email if available
            if (employee.personal_email) {
              setEmail(employee.personal_email)
            }
            
            // Set department if employee has one
            if (employee.department?.department_id) {
              setDepartmentId(employee.department.department_id.toString())
            }
            
            // Set role if employee has one
            if (employee.role?.role_id) {
              setRoleId(employee.role.role_id.toString())
            }
          }
          
        } catch (error) {
          console.error('Failed to load departments and roles:', error)
        } finally {
          setIsInitialLoading(false)
        }
      }
      loadData()
    }
  }, [open, employeeId, defaultEmail, employee])

  // Reset email when dialog opens with new employee
  useEffect(() => {
    if (open && employee?.personal_email) {
      setEmail(employee.personal_email)
    } else if (open && defaultEmail) {
      setEmail(defaultEmail)
    }
  }, [open, employee?.personal_email, defaultEmail])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    console.log('handleSubmit called', { email, departmentId, roleId, employeeId, expiresDays })
    
    if (!email || !departmentId || !roleId) {
      console.log('Missing required fields:', { email, departmentId, roleId })
      return
    }

    try {
      setIsLoading(true)
      
      const invitationData = {
        email,
        department_id: parseInt(departmentId),
        role_id: parseInt(roleId),
        employee_profile_id: employeeId,
        expires_days: parseInt(expiresDays)
      }
      
      console.log('Creating invitation with data:', invitationData)

      const response = await invitationService.createInvitation(invitationData)
      console.log('Invitation created successfully:', response)
      onSuccess(response)
      
      // Reset form
      setEmail(defaultEmail)
      setDepartmentId('')
      setRoleId('')
      setExpiresDays('7')
      onOpenChange(false)
    } catch (error) {
      console.error('Failed to create invitation:', error)
      alert('Failed to create invitation. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  if (!open) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Send Employee Invitation
          </h2>
          <button
            onClick={() => onOpenChange(false)}
            className="text-gray-500 hover:text-gray-700"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="mb-4 text-sm text-gray-600">
          Send an invitation to create a user account for this employee.
        </div>
        
        {isInitialLoading ? (
          <div className="flex items-center justify-center py-6">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label>Email Address</Label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="employee@example.com"
                required
              />
            </div>

            <div className="space-y-2">
              <Label>Department</Label>
              <Select value={departmentId} onValueChange={setDepartmentId} required>
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

            <div className="space-y-2">
              <Label>Role</Label>
              <Select value={roleId} onValueChange={setRoleId} required>
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

            <div className="space-y-2">
              <Label>Expires In (Days)</Label>
              <Select value={expiresDays} onValueChange={setExpiresDays}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="3">3 days</SelectItem>
                  <SelectItem value="7">7 days</SelectItem>
                  <SelectItem value="14">14 days</SelectItem>
                  <SelectItem value="30">30 days</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex justify-end space-x-2 mt-6">
              <button
                type="button"
                onClick={() => onOpenChange(false)}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {isLoading ? 'Sending...' : 'Send Invitation'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

export default InvitationDialog