'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { LayoutWrapper, PermissionProtectedRoute } from '@/components'
import { departmentService } from '@/lib/api'
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
  Building,
  Plus,
  Edit,
  Trash2,
  Search,
  MapPin,
  ArrowUpDown,
  Check,
  X
} from 'lucide-react'

interface Office {
  office_id: number
  office_name: string
  location?: string
}

export default function OfficesPage() {
  const { user } = useAuth()
  const [offices, setOffices] = useState<Office[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingOffice, setEditingOffice] = useState<Office | null>(null)
  const [formData, setFormData] = useState({ office_name: '', location: '' })
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    fetchOffices()
  }, [])

  const fetchOffices = async () => {
    setIsLoading(true)
    try {
      const response = await departmentService.getOffices()
      setOffices(response.data || response)
    } catch (error) {
      console.error('Error fetching offices:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateOffice = async () => {
    if (!formData.office_name.trim()) return

    setIsSubmitting(true)
    setError(null)
    try {
      const response = await departmentService.createOffice({
        office_name: formData.office_name.trim(),
        location: formData.location.trim()
      })
      
      const newOffice = response.data || response
      setOffices([...offices, newOffice])
      setFormData({ office_name: '', location: '' })
      setIsDialogOpen(false)
    } catch (error: any) {
      console.error('Error creating office:', error)
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Failed to create office')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleUpdateOffice = async () => {
    if (!editingOffice || !formData.office_name.trim()) return

    setIsSubmitting(true)
    setError(null)
    try {
      await departmentService.updateOffice(editingOffice.office_id, {
        office_name: formData.office_name.trim(),
        location: formData.location.trim()
      })
      
      setOffices(offices.map(office =>
        office.office_id === editingOffice.office_id
          ? { ...office, office_name: formData.office_name.trim(), location: formData.location.trim() }
          : office
      ))
      setFormData({ office_name: '', location: '' })
      setEditingOffice(null)
      setIsDialogOpen(false)
    } catch (error: any) {
      console.error('Error updating office:', error)
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Failed to update office')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDeleteOffice = async () => {
    if (!officeToDelete) return

    setIsDeleting(true)
    setError(null)
    try {
      await departmentService.deleteOffice(officeToDelete.office_id)
      setOffices(offices.filter(o => o.office_id !== officeToDelete.office_id))
      setDeleteDialogOpen(false)
      setOfficeToDelete(null)
    } catch (error: any) {
      console.error('Error deleting office:', error)
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('Failed to delete office')
      }
    } finally {
      setIsDeleting(false)
    }
  }

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [officeToDelete, setOfficeToDelete] = useState<Office | null>(null)

  const openDeleteDialog = (office: Office) => {
    setOfficeToDelete(office)
    setDeleteDialogOpen(true)
    setError(null)
  }

  const openEditDialog = (office: Office) => {
    setEditingOffice(office)
    setFormData({ office_name: office.office_name, location: office.location || '' })
    setIsDialogOpen(true)
  }

  const openCreateDialog = () => {
    setEditingOffice(null)
    setFormData({ office_name: '', location: '' })
    setError(null)
    setIsDialogOpen(true)
  }

  const filteredOffices = offices.filter(office =>
    office.office_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (office.location && office.location.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  return (
    <PermissionProtectedRoute requiredPermission="system_config">
      <LayoutWrapper>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Offices</h1>
            <p className="text-muted-foreground">Manage office locations and sites</p>
          </div>
          <Button onClick={openCreateDialog}>
            <Plus className="h-4 w-4 mr-2" />
            Add Office
          </Button>
        </div>

        {/* Search */}
        <div className="flex items-center space-x-2">
          <Search className="h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search offices..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="max-w-sm"
          />
        </div>

        {/* Main Content */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Building className="h-5 w-5" />
              <span>Offices ({filteredOffices.length})</span>
            </CardTitle>
            <CardDescription>Manage office locations and sites</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="cursor-pointer hover:bg-accent/50">
                    <div className="flex items-center space-x-1">
                      Office Name
                      <ArrowUpDown className="h-3 w-3" />
                    </div>
                  </TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredOffices.map((office) => (
                  <TableRow key={office.office_id}>
                    <TableCell className="font-semibold">
                      {office.office_name}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <MapPin className="h-4 w-4 text-muted-foreground" />
                        {office.location || 'No location specified'}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEditDialog(office)}
                          title="Edit office"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openDeleteDialog(office)}
                          className="text-destructive hover:text-destructive"
                          title="Delete office"
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

        {/* Create/Edit Office Dialog */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>
                {editingOffice ? 'Edit Office' : 'Create Office'}
              </DialogTitle>
              <DialogDescription>
                {editingOffice
                  ? 'Update the office details below.'
                  : 'Enter a name and location for the new office.'
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
                <Label htmlFor="office_name">Office Name</Label>
                <Input
                  id="office_name"
                  value={formData.office_name}
                  onChange={(e) => setFormData({ ...formData, office_name: e.target.value })}
                  placeholder="Enter office name"
                  autoFocus
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="location">Location</Label>
                <Input
                  id="location"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  placeholder="Enter office location"
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
                onClick={editingOffice ? handleUpdateOffice : handleCreateOffice}
                disabled={isSubmitting || !formData.office_name.trim()}
              >
                {isSubmitting ? 'Saving...' : (editingOffice ? 'Update' : 'Create')}
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
                <span>Delete Office</span>
              </DialogTitle>
              <DialogDescription>
                Are you sure you want to delete "{officeToDelete?.office_name}"? This action cannot be undone.
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
                onClick={handleDeleteOffice}
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