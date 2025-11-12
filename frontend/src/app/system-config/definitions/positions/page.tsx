'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { LayoutWrapper, PermissionProtectedRoute } from '@/components'
import { positionsService, departmentService } from '@/lib/api'
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Briefcase,
  Plus,
  Edit,
  Trash2,
  Search,
  ArrowUpDown,
  Building
} from 'lucide-react'

interface Position {
  position_id: number
  position_name: string
  description?: string
  department_id?: number | null
  created_at?: string
  updated_at?: string
}

interface Department {
  department_id: number
  department_name: string
}

export default function PositionsPage() {
  const { user } = useAuth()
  const [positions, setPositions] = useState<Position[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingPosition, setEditingPosition] = useState<Position | null>(null)
  const [formData, setFormData] = useState({ position_name: '', description: '', department_id: 'none' })
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [positionToDelete, setPositionToDelete] = useState<Position | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    fetchPositions()
    fetchDepartments()
  }, [])

  const fetchPositions = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await positionsService.getPositions()
      setPositions(response.data || response)
    } catch (error) {
      console.error('Error fetching positions:', error)
      setError('Failed to fetch positions')
    } finally {
      setIsLoading(false)
    }
  }

  const fetchDepartments = async () => {
    try {
      const response = await departmentService.getDepartments()
      setDepartments(response.data || response)
    } catch (error) {
      console.error('Error fetching departments:', error)
    }
  }

  const handleCreatePosition = async () => {
    if (!formData.position_name.trim()) return

    setIsSubmitting(true)
    setError(null)
    try {
      const response = await positionsService.createPosition({
        position_name: formData.position_name.trim(),
        description: formData.description.trim(),
        department_id: formData.department_id && formData.department_id !== "none" ? parseInt(formData.department_id) : null
      })
      
      const newPosition = response.data || response
      setPositions([...positions, newPosition])
      setFormData({ position_name: '', description: '', department_id: 'none' })
      setIsDialogOpen(false)
    } catch (error: any) {
      console.error('Error creating position:', error)
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Failed to create position')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleUpdatePosition = async () => {
    if (!editingPosition || !formData.position_name.trim()) return

    setIsSubmitting(true)
    setError(null)
    try {
      await positionsService.updatePosition(editingPosition.position_id, {
        position_name: formData.position_name.trim(),
        description: formData.description.trim(),
        department_id: formData.department_id && formData.department_id !== "none" ? parseInt(formData.department_id) : null
      })
      
      setPositions(positions.map(position =>
        position.position_id === editingPosition.position_id
          ? { ...position, position_name: formData.position_name.trim(), description: formData.description.trim(), department_id: formData.department_id && formData.department_id !== "none" ? parseInt(formData.department_id) : null }
          : position
      ))
      setFormData({ position_name: '', description: '', department_id: 'none' })
      setEditingPosition(null)
      setIsDialogOpen(false)
    } catch (error: any) {
      console.error('Error updating position:', error)
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Failed to update position')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const openDeleteDialog = (position: Position) => {
    setPositionToDelete(position)
    setDeleteDialogOpen(true)
    setError(null)
  }

  const handleDeletePosition = async () => {
    if (!positionToDelete) return

    setIsDeleting(true)
    setError(null)
    try {
      await positionsService.deletePosition(positionToDelete.position_id)
      setPositions(positions.filter(position => position.position_id !== positionToDelete.position_id))
      setDeleteDialogOpen(false)
      setPositionToDelete(null)
    } catch (error: any) {
      console.error('Error deleting position:', error)
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Failed to delete position')
      }
    } finally {
      setIsDeleting(false)
    }
  }

  const openEditDialog = (position: Position) => {
    setEditingPosition(position)
    setFormData({ 
      position_name: position.position_name, 
      description: position.description || '', 
      department_id: position.department_id?.toString() || "none"
    })
    setIsDialogOpen(true)
  }

  const openCreateDialog = () => {
    setEditingPosition(null)
    setFormData({ position_name: '', description: '', department_id: 'none' })
    setError(null)
    setIsDialogOpen(true)
  }

  const getDepartmentName = (departmentId: number | null | undefined) => {
    if (!departmentId) return '-'
    const department = departments.find(d => d.department_id === departmentId)
    return department ? department.department_name : '-'
  }

  const filteredPositions = positions.filter(position =>
    position.position_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (position.description && position.description.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  return (
    <PermissionProtectedRoute requiredPermission="system_config">
      <LayoutWrapper>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Positions</h1>
            <p className="text-muted-foreground">Manage job positions and their departments</p>
          </div>
          <Button onClick={openCreateDialog}>
            <Plus className="h-4 w-4 mr-2" />
            Add Position
          </Button>
        </div>

        {/* Search */}
        <div className="flex items-center space-x-2">
          <Search className="h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search positions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="max-w-sm"
          />
        </div>

        {/* Positions Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Briefcase className="h-5 w-5" />
              <span>Positions ({filteredPositions.length})</span>
            </CardTitle>
            <CardDescription>Manage job positions and their department assignments</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="cursor-pointer hover:bg-accent/50">
                    <div className="flex items-center space-x-1">
                      Position Name
                      <ArrowUpDown className="h-3 w-3" />
                    </div>
                  </TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredPositions.map((position) => (
                  <TableRow key={position.position_id}>
                    <TableCell className="font-semibold">
                      {position.position_name}
                    </TableCell>
                    <TableCell>{position.description || '-'}</TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Building className="h-4 w-4 text-muted-foreground" />
                        {getDepartmentName(position.department_id)}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEditDialog(position)}
                          title="Edit position"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openDeleteDialog(position)}
                          className="text-destructive hover:text-destructive"
                          title="Delete position"
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

        {/* Create/Edit Position Dialog */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>
                {editingPosition ? 'Edit Position' : 'Create Position'}
              </DialogTitle>
              <DialogDescription>
                {editingPosition 
                  ? 'Update the position details below.'
                  : 'Enter a name and description for the new position.'
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
                <Label htmlFor="position_name">Position Name</Label>
                <Input
                  id="position_name"
                  value={formData.position_name}
                  onChange={(e) => setFormData({ ...formData, position_name: e.target.value })}
                  placeholder="Enter position name"
                  autoFocus
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Input
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Enter position description"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="department_id">Department</Label>
                <Select value={formData.department_id} onValueChange={(value) => setFormData({ ...formData, department_id: value })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select department" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">
                      {departments.length === 0 ? "No departments available" : "No department"}
                    </SelectItem>
                    {departments.map((department) => (
                      <SelectItem key={department.department_id} value={department.department_id.toString()}>
                        {department.department_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
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
                onClick={editingPosition ? handleUpdatePosition : handleCreatePosition}
                disabled={isSubmitting || !formData.position_name.trim()}
              >
                {isSubmitting ? 'Saving...' : (editingPosition ? 'Update' : 'Create')}
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
                <span>Delete Position</span>
              </DialogTitle>
              <DialogDescription>
                Are you sure you want to delete "{positionToDelete?.position_name}"? This action cannot be undone.
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
                onClick={handleDeletePosition}
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