'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { LayoutWrapper, PermissionProtectedRoute } from '@/components'
import { roleService, permissionService } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Shield,
  Plus,
  Edit,
  Trash2,
  Search,
  ArrowUpDown,
  Check,
  X
} from 'lucide-react'

interface Role {
  role_id: number
  role_name: string
  description: string
  permissions: Permission[]
}

interface Permission {
  permission_id: number
  permission_name: string
  description: string
}

export default function RolesPage() {
  const { user } = useAuth()
  const [roles, setRoles] = useState<Role[]>([])
  const [permissions, setPermissions] = useState<Permission[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isPermissionDialogOpen, setIsPermissionDialogOpen] = useState(false)
  const [editingRole, setEditingRole] = useState<Role | null>(null)
  const [selectedRole, setSelectedRole] = useState<Role | null>(null)
  const [formData, setFormData] = useState({ role_name: '', description: '' })
  const [selectedPermissions, setSelectedPermissions] = useState<number[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [roleToDelete, setRoleToDelete] = useState<Role | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const [activeTab, setActiveTab] = useState('roles')

  useEffect(() => {
    fetchRoles()
    fetchPermissions()
  }, [])

  const fetchRoles = async () => {
    setIsLoading(true)
    try {
      const response = await roleService.getRoles()
      setRoles(response.data || response)
    } catch (error) {
      console.error('Error fetching roles:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchPermissions = async () => {
    try {
      const response = await permissionService.getPermissions()
      setPermissions(response.data || response)
    } catch (error) {
      console.error('Error fetching permissions:', error)
    }
  }

  const handleCreateRole = async () => {
    if (!formData.role_name.trim()) return

    setIsSubmitting(true)
    setError(null)
    try {
      const response = await roleService.createRole({
        role_name: formData.role_name.trim(),
        description: formData.description.trim()
      })
      
      const newRole = response.data || response
      setRoles([...roles, newRole])
      setFormData({ role_name: '', description: '' })
      setSelectedPermissions([])
      setIsDialogOpen(false)
    } catch (error: any) {
      console.error('Error creating role:', error)
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Failed to create role')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleUpdateRole = async () => {
    if (!editingRole || !formData.role_name.trim()) return

    setIsSubmitting(true)
    setError(null)
    try {
      await roleService.updateRole(editingRole.role_id, {
        role_name: formData.role_name.trim(),
        description: formData.description.trim()
      })
      
      setRoles(roles.map(role =>
        role.role_id === editingRole.role_id
          ? { ...role, role_name: formData.role_name.trim(), description: formData.description.trim() }
          : role
      ))
      setFormData({ role_name: '', description: '' })
      setEditingRole(null)
      setIsDialogOpen(false)
    } catch (error: any) {
      console.error('Error updating role:', error)
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Failed to update role')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const openDeleteDialog = (role: Role) => {
    // Check if role is protected
    if (role.role_name === 'super_admin' || role.role_name === 'admin') {
      setError(`Cannot delete system role: ${role.role_name}`)
      return
    }
    setRoleToDelete(role)
    setDeleteDialogOpen(true)
    setError(null)
  }

  const handleDeleteRole = async () => {
    if (!roleToDelete) return

    setIsDeleting(true)
    setError(null)
    try {
      await roleService.deleteRole(roleToDelete.role_id)
      setRoles(roles.filter(r => r.role_id !== roleToDelete.role_id))
      setDeleteDialogOpen(false)
      setRoleToDelete(null)
    } catch (error: any) {
      console.error('Error deleting role:', error)
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Failed to delete role')
      }
    } finally {
      setIsDeleting(false)
    }
  }

  const handleAssignPermissions = async () => {
    if (!selectedRole) return

    setIsSubmitting(true)
    try {
      await roleService.assignPermissionsToRole(selectedRole.role_id, selectedPermissions)
      
      // Refetch roles to get updated permissions
      await fetchRoles()
      
      setSelectedPermissions([])
      setSelectedRole(null)
      setIsPermissionDialogOpen(false)
    } catch (error) {
      console.error('Error assigning permissions:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const openEditDialog = (role: Role) => {
    // Prevent editing of protected roles
    if (role.role_name === 'super_admin' || role.role_name === 'admin') {
      alert(`Cannot edit system role: ${role.role_name}`)
      return
    }
    setEditingRole(role)
    setFormData({ role_name: role.role_name, description: role.description })
    setIsDialogOpen(true)
  }

  const openCreateDialog = () => {
    setEditingRole(null)
    setFormData({ role_name: '', description: '' })
    setSelectedPermissions([])
    setError(null)
    setIsDialogOpen(true)
  }

  const openPermissionDialog = (role: Role) => {
    setSelectedRole(role)
    setSelectedPermissions((role.permissions || []).map(p => p.permission_id))
    setIsPermissionDialogOpen(true)
  }

  const togglePermission = (permissionId: number) => {
    setSelectedPermissions(prev => 
      prev.includes(permissionId)
        ? prev.filter(id => id !== permissionId)
        : [...prev, permissionId]
    )
  }

  const filteredRoles = roles.filter(role =>
    role.role_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    role.description.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <PermissionProtectedRoute requiredPermission="system_config">
      <LayoutWrapper>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Roles & Permissions</h1>
            <p className="text-muted-foreground">Manage user roles and their permissions</p>
          </div>
          <Button onClick={openCreateDialog}>
            <Plus className="h-4 w-4 mr-2" />
            Add Role
          </Button>
        </div>

        {/* Search */}
        <div className="flex items-center space-x-2">
          <Search className="h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search roles..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="max-w-sm"
          />
        </div>

        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="roles">Roles</TabsTrigger>
            <TabsTrigger value="permissions">All Permissions</TabsTrigger>
          </TabsList>

          <TabsContent value="roles" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Shield className="h-5 w-5" />
                  <span>Roles ({filteredRoles.length})</span>
                </CardTitle>
                <CardDescription>Manage user roles and their assigned permissions</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="cursor-pointer hover:bg-accent/50">
                        <div className="flex items-center space-x-1">
                          Role Name
                          <ArrowUpDown className="h-3 w-3" />
                        </div>
                      </TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-center">Permissions</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredRoles.map((role) => (
                      <TableRow key={role.role_id}>
                        <TableCell className="font-semibold">
                          <div className="flex items-center space-x-3">
                            {role.role_name}
                            {(role.role_name === 'super_admin' || role.role_name === 'admin') && (
                              <Badge variant="destructive" className="text-xs ml-2">Protected</Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>{role.description}</TableCell>
                        <TableCell className="text-center">
                          <Badge variant="secondary" className="ml-2">{role.permissions?.length || 0} permissions</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end space-x-2">
                            {/* Only show Manage Permissions for non-super_admin roles */}
                            {role.role_name !== 'super_admin' && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => openPermissionDialog(role)}
                                className="text-blue-600 hover:text-blue-800 hover:bg-blue-50"
                              >
                                Manage Permissions
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openEditDialog(role)}
                              disabled={role.role_name === 'super_admin' || role.role_name === 'admin'}
                              title={role.role_name === 'super_admin' || role.role_name === 'admin' ? 'Cannot edit system role' : 'Edit role'}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openDeleteDialog(role)}
                              className="text-destructive hover:text-destructive"
                              disabled={role.role_name === 'super_admin' || role.role_name === 'admin'}
                              title={role.role_name === 'super_admin' || role.role_name === 'admin' ? 'Cannot delete system role' : 'Delete role'}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="permissions" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>All Permissions ({permissions.length})</CardTitle>
                <CardDescription>View all available system permissions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {permissions.map((permission) => (
                    <div key={permission.permission_id} className="p-4 border rounded-lg">
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-semibold">{permission.permission_name}</h4>
                          <p className="text-sm text-muted-foreground mt-1">{permission.description}</p>
                        </div>
                        <Badge variant="outline" className="ml-2">ID: {permission.permission_id}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Create/Edit Role Dialog */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>
                {editingRole ? 'Edit Role' : 'Create Role'}
              </DialogTitle>
              <DialogDescription>
                {editingRole
                  ? 'Update the role details below.'
                  : 'Enter a name and description for the new role.'
                }
              </DialogDescription>
            </DialogHeader>
            
            {/* Error Alert inside dialog */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded mb-3 text-sm">
                <div className="flex items-center">
                  <span>{error}</span>
                  <button
                    onClick={() => setError(null)}
                    className="ml-auto text-red-500 hover:text-red-700 font-bold text-lg leading-none"
                  >
                    ×
                  </button>
                </div>
              </div>
            )}
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="role_name">Role Name</Label>
                <Input
                  id="role_name"
                  value={formData.role_name}
                  onChange={(e) => setFormData({ ...formData, role_name: e.target.value })}
                  placeholder="Enter role name"
                  autoFocus
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Input
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Enter role description"
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setIsDialogOpen(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                onClick={editingRole ? handleUpdateRole : handleCreateRole}
                disabled={isSubmitting || !formData.role_name.trim()}
              >
                {isSubmitting ? 'Saving...' : (editingRole ? 'Update' : 'Create')}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Assign Permissions Dialog */}
        <Dialog open={isPermissionDialogOpen} onOpenChange={setIsPermissionDialogOpen}>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle>Assign Permissions - {selectedRole?.role_name}</DialogTitle>
              <DialogDescription>
                Select the permissions to assign to this role.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="flex items-center justify-between p-2 border rounded-lg bg-muted/50">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    checked={selectedPermissions.length === permissions.length}
                    onCheckedChange={(checked) => {
                      if (checked) {
                        setSelectedPermissions(permissions.map(p => p.permission_id))
                      } else {
                        setSelectedPermissions([])
                      }
                    }}
                  />
                  <span className="text-sm font-medium">Select All ({selectedPermissions.length} selected)</span>
                </div>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedPermissions([])}
                  >
                    Clear
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedPermissions(permissions.map(p => p.permission_id))}
                  >
                    All
                  </Button>
                </div>
              </div>
              <div className="max-h-[300px] overflow-y-auto space-y-2">
                {permissions.map((permission) => (
                  <div key={permission.permission_id} className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-muted/50 transition-colors">
                    <Checkbox
                      checked={selectedPermissions.includes(permission.permission_id)}
                      onCheckedChange={() => togglePermission(permission.permission_id)}
                    />
                    <div className="flex-1">
                      <div className="font-medium">{permission.permission_name}</div>
                      <div className="text-sm text-muted-foreground">{permission.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setIsPermissionDialogOpen(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                onClick={handleAssignPermissions}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Assigning...' : `Assign ${selectedPermissions.length} Permissions`}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle className="flex items-center space-x-2">
                <Trash2 className="h-5 w-5 text-destructive" />
                <span>Delete Role</span>
              </DialogTitle>
              <DialogDescription>
                Are you sure you want to delete "{roleToDelete?.role_name}"? This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            
            {/* Error Alert inside delete dialog */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded mb-3 text-sm">
                <div className="flex items-center">
                  <span>{error}</span>
                  <button
                    onClick={() => setError(null)}
                    className="ml-auto text-red-500 hover:text-red-700 font-bold text-lg leading-none"
                  >
                    ×
                  </button>
                </div>
              </div>
            )}
            
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setDeleteDialogOpen(false)}
                disabled={isDeleting}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleDeleteRole}
                disabled={isDeleting}
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
      </LayoutWrapper>
    </PermissionProtectedRoute>
  )
}