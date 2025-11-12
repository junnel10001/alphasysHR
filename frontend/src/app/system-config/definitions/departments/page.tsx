'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { LayoutWrapper } from '@/components/layout'
import { departmentService } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  Building,
  Plus,
  Edit,
  Trash2,
  Search,
  ArrowUpDown
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

interface Department {
  department_id: number
  department_name: string
}

export default function DepartmentsPage() {
  const { user } = useAuth()
  const [departments, setDepartments] = useState<Department[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingDepartment, setEditingDepartment] = useState<Department | null>(null)
  const [formData, setFormData] = useState({ department_name: '' })
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [departmentToDelete, setDepartmentToDelete] = useState<Department | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    fetchDepartments()
  }, [])

  const fetchDepartments = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await departmentService.getDepartments()
      setDepartments(response.data || response)
    } catch (error) {
      console.error('Error fetching departments:', error)
      setError('Failed to fetch departments')
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!formData.department_name.trim()) return

    setIsSubmitting(true)
    setError(null)
    try {
      const response = await departmentService.createDepartment({
        department_name: formData.department_name.trim()
      })
      
      const newDepartment = response.data || response
      setDepartments([...departments, newDepartment])
      setFormData({ department_name: '' })
      setIsDialogOpen(false)
    } catch (error: any) {
      console.error('Error creating department:', error)
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Failed to create department')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleUpdate = async () => {
    if (!editingDepartment || !formData.department_name.trim()) return

    setIsSubmitting(true)
    setError(null)
    try {
      await departmentService.updateDepartment(editingDepartment.department_id, {
        department_name: formData.department_name.trim()
      })
      
      setDepartments(departments.map(dept =>
        dept.department_id === editingDepartment.department_id
          ? { ...dept, department_name: formData.department_name.trim() }
          : dept
      ))
      setFormData({ department_name: '' })
      setEditingDepartment(null)
      setIsDialogOpen(false)
    } catch (error: any) {
      console.error('Error updating department:', error)
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Failed to update department')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const openDeleteDialog = (department: Department) => {
    setDepartmentToDelete(department)
    setDeleteDialogOpen(true)
    setError(null)
  }

  const handleDelete = async () => {
    if (!departmentToDelete) return

    setIsDeleting(true)
    setError(null)
    try {
      await departmentService.deleteDepartment(departmentToDelete.department_id)
      setDepartments(departments.filter(dept => dept.department_id !== departmentToDelete.department_id))
      setDeleteDialogOpen(false)
      setDepartmentToDelete(null)
    } catch (error: any) {
      console.error('Error deleting department:', error)
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Failed to delete department')
      }
    } finally {
      setIsDeleting(false)
    }
  }

  const openEditDialog = (department: Department) => {
    setEditingDepartment(department)
    setFormData({ department_name: department.department_name })
    setIsDialogOpen(true)
  }

  const openCreateDialog = () => {
    setEditingDepartment(null)
    setFormData({ department_name: '' })
    setError(null)
    setIsDialogOpen(true)
  }

  const filteredDepartments = departments.filter(dept =>
    dept.department_name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (isLoading) {
    return (
      <LayoutWrapper>
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
        </div>
      </LayoutWrapper>
    )
  }

  return (
    <LayoutWrapper>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Departments</h1>
            <p className="text-muted-foreground">Manage organizational departments</p>
          </div>
          <Button onClick={openCreateDialog}>
            <Plus className="h-4 w-4 mr-2" />
            Add Department
          </Button>
        </div>

        {/* Search */}
        <div className="flex items-center space-x-2">
          <Search className="h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search departments..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="max-w-sm"
          />
        </div>

        {/* Departments Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Building className="h-5 w-5" />
              <span>Departments ({filteredDepartments.length})</span>
            </CardTitle>
            <CardDescription>Manage organizational departments</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="cursor-pointer hover:bg-accent/50">
                    <div className="flex items-center space-x-1">
                      Department Name
                      <ArrowUpDown className="h-3 w-3" />
                    </div>
                  </TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDepartments.map((department) => (
                  <TableRow key={department.department_id}>
                    <TableCell>{department.department_name}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEditDialog(department)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openDeleteDialog(department)}
                          className="text-destructive hover:text-destructive"
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

        {/* Create/Edit Dialog */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>
                {editingDepartment ? 'Edit Department' : 'Create Department'}
              </DialogTitle>
              <DialogDescription>
                {editingDepartment
                  ? 'Update the department name below.'
                  : 'Enter a name for the new department below.'
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
                <Label htmlFor="department_name">Department Name</Label>
                <Input
                  id="department_name"
                  value={formData.department_name}
                  onChange={(e) => setFormData({ department_name: e.target.value })}
                  placeholder="Enter department name"
                  autoFocus
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
                onClick={editingDepartment ? handleUpdate : handleCreate}
                disabled={isSubmitting || !formData.department_name.trim()}
              >
                {isSubmitting ? 'Saving...' : (editingDepartment ? 'Update' : 'Create')}
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
                <span>Delete Department</span>
              </DialogTitle>
              <DialogDescription>
                Are you sure you want to delete "{departmentToDelete?.department_name}"? This action cannot be undone.
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
                onClick={handleDelete}
                disabled={isDeleting}
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </LayoutWrapper>
  )
}