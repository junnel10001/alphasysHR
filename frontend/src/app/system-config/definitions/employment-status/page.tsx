'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { LayoutWrapper, PermissionProtectedRoute } from '@/components'
import { employmentStatusesService } from '@/lib/api'
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
  Users,
  Plus,
  Edit,
  Trash2,
  Search,
  ArrowUpDown,
  Check,
  X
} from 'lucide-react'

interface EmploymentStatus {
  employment_status_id: number
  status_name: string
  description?: string
  is_active: boolean
  created_at?: string
  updated_at?: string
}

export default function EmploymentStatusPage() {
  const { user } = useAuth()
  const [employmentStatuses, setEmploymentStatuses] = useState<EmploymentStatus[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingStatus, setEditingStatus] = useState<EmploymentStatus | null>(null)
  const [formData, setFormData] = useState({ status_name: '', description: '', is_active: true })
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [statusToDelete, setStatusToDelete] = useState<EmploymentStatus | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    fetchEmploymentStatuses()
  }, [])

  const fetchEmploymentStatuses = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await employmentStatusesService.getEmploymentStatuses()
      setEmploymentStatuses(response.data || response)
    } catch (error) {
      console.error('Error fetching employment statuses:', error)
      setError('Failed to fetch employment statuses')
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateStatus = async () => {
    if (!formData.status_name.trim()) return

    setIsSubmitting(true)
    setError(null)
    try {
      const response = await employmentStatusesService.createEmploymentStatus({
        status_name: formData.status_name.trim(),
        description: formData.description.trim(),
        is_active: formData.is_active
      })
      
      const newStatus = response.data || response
      setEmploymentStatuses([...employmentStatuses, newStatus])
      setFormData({ status_name: '', description: '', is_active: true })
      setIsDialogOpen(false)
    } catch (error: any) {
      console.error('Error creating employment status:', error)
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Failed to create employment status')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleUpdateStatus = async () => {
    if (!editingStatus || !formData.status_name.trim()) return

    setIsSubmitting(true)
    setError(null)
    try {
      await employmentStatusesService.updateEmploymentStatus(editingStatus.employment_status_id, {
        status_name: formData.status_name.trim(),
        description: formData.description.trim(),
        is_active: formData.is_active
      })
      
      setEmploymentStatuses(employmentStatuses.map(status =>
        status.employment_status_id === editingStatus.employment_status_id
          ? { ...status, status_name: formData.status_name.trim(), description: formData.description.trim(), is_active: formData.is_active }
          : status
      ))
      setFormData({ status_name: '', description: '', is_active: true })
      setEditingStatus(null)
      setIsDialogOpen(false)
    } catch (error: any) {
      console.error('Error updating employment status:', error)
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Failed to update employment status')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const openDeleteDialog = (status: EmploymentStatus) => {
    setStatusToDelete(status)
    setDeleteDialogOpen(true)
    setError(null)
  }

  const handleDeleteStatus = async () => {
    if (!statusToDelete) return

    setIsDeleting(true)
    setError(null)
    try {
      await employmentStatusesService.deleteEmploymentStatus(statusToDelete.employment_status_id)
      setEmploymentStatuses(employmentStatuses.filter(status => status.employment_status_id !== statusToDelete.employment_status_id))
      setDeleteDialogOpen(false)
      setStatusToDelete(null)
    } catch (error: any) {
      console.error('Error deleting employment status:', error)
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Failed to delete employment status')
      }
    } finally {
      setIsDeleting(false)
    }
  }

  const openEditDialog = (status: EmploymentStatus) => {
    setEditingStatus(status)
    setFormData({ 
      status_name: status.status_name, 
      description: status.description || '', 
      is_active: status.is_active 
    })
    setIsDialogOpen(true)
  }

  const openCreateDialog = () => {
    setEditingStatus(null)
    setFormData({ status_name: '', description: '', is_active: true })
    setError(null)
    setIsDialogOpen(true)
  }

  const filteredStatuses = employmentStatuses.filter(status =>
    status.status_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (status.description && status.description.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  return (
    <PermissionProtectedRoute requiredPermission="system_config">
      <LayoutWrapper>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Employment Status</h1>
              <p className="text-muted-foreground">Manage employment status types</p>
            </div>
            <Button onClick={openCreateDialog}>
              <Plus className="h-4 w-4 mr-2" />
              Add Status
            </Button>
          </div>

          {/* Search */}
          <div className="flex items-center space-x-2">
            <Search className="h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search employment statuses..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="max-w-sm"
            />
          </div>

          {/* Employment Status Table */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Users className="h-5 w-5" />
                <span>Employment Status ({filteredStatuses.length})</span>
              </CardTitle>
              <CardDescription>Manage employment status types and their active status</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="cursor-pointer hover:bg-accent/50">
                      <div className="flex items-center space-x-1">
                        Status Name
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredStatuses.map((status) => (
                    <TableRow key={status.employment_status_id}>
                      <TableCell className="font-semibold">
                        <div className="flex items-center space-x-2">
                          {status.status_name}
                          {!status.is_active && (
                            <Badge variant="secondary" className="text-xs ml-2">Inactive</Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{status.description || '-'}</TableCell>
                      <TableCell>
                        <Badge variant={status.is_active ? "default" : "secondary"}>
                          {status.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openEditDialog(status)}
                            title="Edit employment status"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openDeleteDialog(status)}
                            className="text-destructive hover:text-destructive"
                            title="Delete employment status"
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

          {/* Create/Edit Status Dialog */}
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogContent className="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>
                  {editingStatus ? 'Edit Employment Status' : 'Create Employment Status'}
                </DialogTitle>
                <DialogDescription>
                  {editingStatus 
                    ? 'Update the employment status details below.'
                    : 'Enter a name and description for the new employment status.'
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
                  <Label htmlFor="status_name">Status Name</Label>
                  <Input
                    id="status_name"
                    value={formData.status_name}
                    onChange={(e) => setFormData({ ...formData, status_name: e.target.value })}
                    placeholder="Enter status name"
                    autoFocus
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Input
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Enter status description"
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="h-4 w-4"
                  />
                  <Label htmlFor="is_active" className="text-sm font-medium">
                    Active
                  </Label>
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
                  onClick={editingStatus ? handleUpdateStatus : handleCreateStatus}
                  disabled={isSubmitting || !formData.status_name.trim()}
                >
                  {isSubmitting ? 'Saving...' : (editingStatus ? 'Update' : 'Create')}
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
                  <span>Delete Employment Status</span>
                </DialogTitle>
                <DialogDescription>
                  Are you sure you want to delete "{statusToDelete?.status_name}"? This action cannot be undone.
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
                  onClick={handleDeleteStatus}
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