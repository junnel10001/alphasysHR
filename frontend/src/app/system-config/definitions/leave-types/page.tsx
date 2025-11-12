'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { LayoutWrapper, PermissionProtectedRoute } from '@/components'
import { leaveTypesService } from '@/lib/api'
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
  Calendar,
  Plus,
  Edit,
  Trash2,
  Search,
  ArrowUpDown
} from 'lucide-react'

interface LeaveType {
  leave_type_id: number
  leave_name: string
  description?: string
  default_allocation: number
}

export default function LeaveTypesPage() {
  const { user } = useAuth()
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingLeaveType, setEditingLeaveType] = useState<LeaveType | null>(null)
  const [formData, setFormData] = useState({ leave_name: '', description: '', default_allocation: 0 })
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [leaveTypeToDelete, setLeaveTypeToDelete] = useState<LeaveType | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    fetchLeaveTypes()
  }, [])

  const fetchLeaveTypes = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await leaveTypesService.getLeaveTypes()
      setLeaveTypes(response.data || response)
    } catch (error) {
      console.error('Error fetching leave types:', error)
      setError('Failed to fetch leave types')
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateLeaveType = async () => {
    if (!formData.leave_name.trim()) return

    setIsSubmitting(true)
    setError(null)
    try {
      const response = await leaveTypesService.createLeaveType({
        leave_name: formData.leave_name.trim(),
        description: formData.description.trim(),
        default_allocation: formData.default_allocation
      })
      
      const newLeaveType = response.data || response
      setLeaveTypes([...leaveTypes, newLeaveType])
      setFormData({ leave_name: '', description: '', default_allocation: 0 })
      setIsDialogOpen(false)
    } catch (error: any) {
      console.error('Error creating leave type:', error)
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Failed to create leave type')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleUpdateLeaveType = async () => {
    if (!editingLeaveType || !formData.leave_name.trim()) return

    setIsSubmitting(true)
    setError(null)
    try {
      await leaveTypesService.updateLeaveType(editingLeaveType.leave_type_id, {
        leave_name: formData.leave_name.trim(),
        description: formData.description.trim(),
        default_allocation: formData.default_allocation
      })
      
      setLeaveTypes(leaveTypes.map(type =>
        type.leave_type_id === editingLeaveType.leave_type_id
          ? { ...type, leave_name: formData.leave_name.trim(), description: formData.description.trim(), default_allocation: formData.default_allocation }
          : type
      ))
      setFormData({ leave_name: '', description: '', default_allocation: 0 })
      setEditingLeaveType(null)
      setIsDialogOpen(false)
    } catch (error: any) {
      console.error('Error updating leave type:', error)
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Failed to update leave type')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const openDeleteDialog = (leaveType: LeaveType) => {
    setLeaveTypeToDelete(leaveType)
    setDeleteDialogOpen(true)
    setError(null)
  }

  const handleDeleteLeaveType = async () => {
    if (!leaveTypeToDelete) return

    setIsDeleting(true)
    setError(null)
    try {
      await leaveTypesService.deleteLeaveType(leaveTypeToDelete.leave_type_id)
      setLeaveTypes(leaveTypes.filter(type => type.leave_type_id !== leaveTypeToDelete.leave_type_id))
      setDeleteDialogOpen(false)
      setLeaveTypeToDelete(null)
    } catch (error: any) {
      console.error('Error deleting leave type:', error)
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Failed to delete leave type')
      }
    } finally {
      setIsDeleting(false)
    }
  }

  const openEditDialog = (leaveType: LeaveType) => {
    setEditingLeaveType(leaveType)
    setFormData({ 
      leave_name: leaveType.leave_name, 
      description: leaveType.description || '', 
      default_allocation: leaveType.default_allocation 
    })
    setIsDialogOpen(true)
  }

  const openCreateDialog = () => {
    setEditingLeaveType(null)
    setFormData({ leave_name: '', description: '', default_allocation: 0 })
    setError(null)
    setIsDialogOpen(true)
  }

  const filteredLeaveTypes = leaveTypes.filter(type =>
    type.leave_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (type.description && type.description.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  return (
    <PermissionProtectedRoute requiredPermission="system_config">
      <LayoutWrapper>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Leave Types</h1>
            <p className="text-muted-foreground">Manage leave type definitions and allocations</p>
          </div>
          <Button onClick={openCreateDialog}>
            <Plus className="h-4 w-4 mr-2" />
            Add Leave Type
          </Button>
        </div>

        {/* Search */}
        <div className="flex items-center space-x-2">
          <Search className="h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search leave types..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="max-w-sm"
          />
        </div>

        {/* Leave Types Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Calendar className="h-5 w-5" />
              <span>Leave Types ({filteredLeaveTypes.length})</span>
            </CardTitle>
            <CardDescription>Manage leave type definitions and default allocations</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="cursor-pointer hover:bg-accent/50">
                    <div className="flex items-center space-x-1">
                      Leave Type Name
                      <ArrowUpDown className="h-3 w-3" />
                    </div>
                  </TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Default Allocation (Days)</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredLeaveTypes.map((leaveType) => (
                  <TableRow key={leaveType.leave_type_id}>
                    <TableCell className="font-semibold">
                      {leaveType.leave_name}
                    </TableCell>
                    <TableCell>{leaveType.description || '-'}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{leaveType.default_allocation} days</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEditDialog(leaveType)}
                          title="Edit leave type"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openDeleteDialog(leaveType)}
                          className="text-destructive hover:text-destructive"
                          title="Delete leave type"
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

        {/* Create/Edit Leave Type Dialog */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>
                {editingLeaveType ? 'Edit Leave Type' : 'Create Leave Type'}
              </DialogTitle>
              <DialogDescription>
                {editingLeaveType 
                  ? 'Update the leave type details below.'
                  : 'Enter a name and description for the new leave type.'
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
                <Label htmlFor="leave_name">Leave Type Name</Label>
                <Input
                  id="leave_name"
                  value={formData.leave_name}
                  onChange={(e) => setFormData({ ...formData, leave_name: e.target.value })}
                  placeholder="Enter leave type name"
                  autoFocus
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Input
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Enter leave type description"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="default_allocation">Default Allocation (Days)</Label>
                <Input
                  id="default_allocation"
                  type="number"
                  value={formData.default_allocation}
                  onChange={(e) => setFormData({ ...formData, default_allocation: parseInt(e.target.value) || 0 })}
                  placeholder="Enter default allocation in days"
                  min="0"
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
                onClick={editingLeaveType ? handleUpdateLeaveType : handleCreateLeaveType}
                disabled={isSubmitting || !formData.leave_name.trim()}
              >
                {isSubmitting ? 'Saving...' : (editingLeaveType ? 'Update' : 'Create')}
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
                <span>Delete Leave Type</span>
              </DialogTitle>
              <DialogDescription>
                Are you sure you want to delete "{leaveTypeToDelete?.leave_name}"? This action cannot be undone.
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
                onClick={handleDeleteLeaveType}
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