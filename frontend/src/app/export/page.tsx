'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { Layout } from '@/components/ui/layout'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Download,
  FileText,
  User,
  Calendar,
  Database,
  CheckCircle,
  XCircle,
  AlertCircle,
  Eye,
  Trash2,
  Search,
  RefreshCw,
  Filter,
  FileSpreadsheet,
  FileArchive,
  FileJson,
  File,
  Loader2,
  Play,
  Clock
} from 'lucide-react'
import { format } from 'date-fns'

interface ExportRecord {
  export_id: number
  export_type: string
  format: string
  record_count: number
  generated_by: string
  generated_date: string
  status: 'Completed' | 'Processing' | 'Failed' | 'Scheduled'
  file_url?: string
  file_size?: string
}

interface ExportHistory {
  export_id: number
  type: string
  format: string
  records: number
  generated_by: string
  generated_date: string
  status: 'Completed' | 'Processing' | 'Failed' | 'Scheduled'
  file_size?: string
}

interface ExportStats {
  total_exports: number
  successful_exports: number
  failed_exports: number
  available_formats: string[]
  available_data_types: string[]
}

interface Department {
  department_id: number
  department_name: string
}

export default function ExportPage() {
  const { user, logout } = useAuth()
  const [exportRecords, setExportRecords] = useState<ExportRecord[]>([])
  const [filteredRecords, setFilteredRecords] = useState<ExportRecord[]>([])
  const [exportHistory, setExportHistory] = useState<ExportHistory[]>([])
  const [exportStats, setExportStats] = useState<ExportStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedRecord, setSelectedRecord] = useState<ExportRecord | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filters, setFilters] = useState({
    status: '',
    type: ''
  })
  
  // Export form state
  const [exportForm, setExportForm] = useState({
    data_type: '',
    format_type: '',
    start_date: '',
    end_date: '',
    department_id: '',
    user_id: ''
  })
  
  // Export progress state
  const [isExporting, setIsExporting] = useState(false)
  const [exportProgress, setExportProgress] = useState(0)
  const [exportMessage, setExportMessage] = useState('')
  
  // Departments state
  const [departments, setDepartments] = useState<Department[]>([])
  
  // Available formats and types from backend
  const [availableFormats] = useState(['csv', 'excel', 'pdf', 'json', 'zip'])
  const [availableDataTypes] = useState(['employees', 'payroll', 'overtime', 'activities', 'all'])

  // Fetch initial data
  useEffect(() => {
    fetchExportData()
    fetchDepartments()
  }, [])

  const fetchExportData = async () => {
    try {
      setIsLoading(true)
      
      // Fetch export statistics
      const statsResponse = await fetch('/api/export/stats')
      if (statsResponse.ok) {
        const stats = await statsResponse.json()
        setExportStats(stats)
      }
      
      // Fetch export records (mock data for now, would be real API in production)
      const mockExportRecords: ExportRecord[] = [
        {
          export_id: 1,
          export_type: 'Employee List',
          format: 'Excel',
          record_count: 45,
          generated_by: 'Admin User',
          generated_date: '2024-01-15',
          status: 'Completed',
          file_url: '/exports/employees_2024-01-15.xlsx',
          file_size: '245 KB'
        },
        {
          export_id: 2,
          export_type: 'Attendance Report',
          format: 'PDF',
          record_count: 120,
          generated_by: 'Jane Smith',
          generated_date: '2024-01-14',
          status: 'Completed',
          file_url: '/exports/attendance_2024-01-14.pdf',
          file_size: '1.2 MB'
        },
        {
          export_id: 3,
          export_type: 'Payroll Summary',
          format: 'CSV',
          record_count: 30,
          generated_by: 'Admin User',
          generated_date: '2024-01-13',
          status: 'Processing'
        }
      ]
      
      setExportRecords(mockExportRecords)
      setFilteredRecords(mockExportRecords)
      
      // Mock export history
      const mockExportHistory: ExportHistory[] = [
        {
          export_id: 1,
          type: 'Employee List',
          format: 'Excel',
          records: 45,
          generated_by: 'Admin User',
          generated_date: '2024-01-15',
          status: 'Completed',
          file_size: '245 KB'
        },
        {
          export_id: 2,
          type: 'Attendance Report',
          format: 'PDF',
          records: 120,
          generated_by: 'Jane Smith',
          generated_date: '2024-01-14',
          status: 'Completed',
          file_size: '1.2 MB'
        },
        {
          export_id: 3,
          type: 'Leave Report',
          format: 'Excel',
          records: 15,
          generated_by: 'Bob Johnson',
          generated_date: '2024-01-12',
          status: 'Failed'
        }
      ]
      
      setExportHistory(mockExportHistory)
      
    } catch (error) {
      console.error('Error fetching export data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchDepartments = async () => {
    try {
      const response = await fetch('/api/export/departments')
      if (response.ok) {
        const data = await response.json()
        setDepartments(data)
      }
    } catch (error) {
      console.error('Error fetching departments:', error)
    }
  }

  useEffect(() => {
    applyFilters()
  }, [exportRecords, searchTerm, filters])

  const applyFilters = () => {
    let filtered = [...exportRecords]

    // Apply search term
    if (searchTerm) {
      filtered = filtered.filter(record => 
        record.export_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        record.format.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Apply status filter
    if (filters.status) {
      filtered = filtered.filter(record => record.status === filters.status)
    }

    // Apply type filter
    if (filters.type) {
      filtered = filtered.filter(record => record.export_type === filters.type)
    }

    setFilteredRecords(filtered)
  }

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      'Completed': { label: 'Completed', color: 'bg-green-100 text-green-800', icon: CheckCircle },
      'Processing': { label: 'Processing', color: 'bg-blue-100 text-blue-800', icon: Loader2 },
      'Failed': { label: 'Failed', color: 'bg-red-100 text-red-800', icon: XCircle },
      'Scheduled': { label: 'Scheduled', color: 'bg-yellow-100 text-yellow-800', icon: Clock }
    }
    
    const config = statusConfig[status as keyof typeof statusConfig]
    if (!config) return <Badge variant="secondary">{status}</Badge>
    
    const Icon = config.icon
    return (
      <Badge className={`${config.color} flex items-center`}>
        <Icon className="h-3 w-3 mr-1" />
        {config.label}
      </Badge>
    )
  }

  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'MMM dd, yyyy HH:mm')
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const handleDelete = async (id: number) => {
    try {
      // In a real app, this would call an API
      setExportRecords(prev => prev.filter(record => record.export_id !== id))
      alert('Export record deleted successfully')
    } catch (error) {
      console.error('Error deleting export record:', error)
    }
  }

  const handleDownload = async (fileUrl: string, fileName: string) => {
    try {
      // Create a temporary link to download the file
      const link = document.createElement('a')
      link.href = fileUrl
      link.download = fileName
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      alert('File downloaded successfully')
    } catch (error) {
      console.error('Error downloading file:', error)
    }
  }

  const handleGenerateExport = async () => {
    if (!exportForm.data_type || !exportForm.format_type) {
      alert('Please select both data type and format')
      return
    }

    setIsExporting(true)
    setExportProgress(0)
    setExportMessage('Starting export...')

    try {
      // Simulate export progress
      const progressInterval = setInterval(() => {
        setExportProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      const exportRequest = {
        data_type: exportForm.data_type,
        format_type: exportForm.format_type,
        start_date: exportForm.start_date ? new Date(exportForm.start_date) : undefined,
        end_date: exportForm.end_date ? new Date(exportForm.end_date) : undefined,
        department_id: exportForm.department_id ? parseInt(exportForm.department_id) : undefined,
        user_id: exportForm.user_id ? parseInt(exportForm.user_id) : undefined
      }

      const response = await fetch('/api/export/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(exportRequest),
      })

      clearInterval(progressInterval)
      setExportProgress(100)

      if (response.ok) {
        const result = await response.json()
        if (result.success !== false) {
          setExportMessage(`Export completed successfully: ${result.file_name}`)
          alert(`Export generated successfully: ${result.file_name}`)
          fetchExportData() // Refresh the data
          setIsDialogOpen(false)
          resetExportForm()
        } else {
          setExportMessage(`Export failed: ${result.message || 'Unknown error'}`)
          alert(`Export failed: ${result.message || 'Unknown error'}`)
        }
      } else {
        setExportMessage('Export failed. Please try again.')
        alert('Failed to generate export')
      }
    } catch (error) {
      console.error('Error generating export:', error)
      setExportMessage('Error generating export')
      alert('Error generating export')
    } finally {
      setIsExporting(false)
      // Reset progress after delay
      setTimeout(() => setExportProgress(0), 2000)
    }
  }

  const resetExportForm = () => {
    setExportForm({
      data_type: '',
      format_type: '',
      start_date: '',
      end_date: '',
      department_id: '',
      user_id: ''
    })
  }

  const totalExports = exportRecords.length
  const totalRecords = exportRecords.reduce((sum, record) => sum + record.record_count, 0)
  const completedExports = exportRecords.filter(r => r.status === 'Completed').length

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return (
    <ProtectedRoute requiredRole="admin">
      <Layout>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Data Export</h1>
              <p className="text-muted-foreground">Export system data in various formats</p>
            </div>
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <FileSpreadsheet className="mr-2 h-4 w-4" />
                  New Export
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle>Create Export</DialogTitle>
                  <DialogDescription>
                    Generate a new data export file with custom filters.
                  </DialogDescription>
                </DialogHeader>
                <form className="space-y-4" onSubmit={(e) => {
                  e.preventDefault()
                  handleGenerateExport()
                }}>
                  <div className="space-y-2">
                    <Label htmlFor="dataType">Data Type</Label>
                    <Select
                      value={exportForm.data_type || "employees"}
                      onValueChange={(value) => setExportForm(prev => ({ ...prev, data_type: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select data type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="employees">Employee List</SelectItem>
                        <SelectItem value="payroll">Payroll Summary</SelectItem>
                        <SelectItem value="overtime">Overtime Report</SelectItem>
                        <SelectItem value="activities">Activity Log</SelectItem>
                        <SelectItem value="all">All Data</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="formatType">Export Format</Label>
                    <Select
                      value={exportForm.format_type || "csv"}
                      onValueChange={(value) => setExportForm(prev => ({ ...prev, format_type: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select format" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="csv">CSV (.csv)</SelectItem>
                        <SelectItem value="excel">Excel (.xlsx)</SelectItem>
                        <SelectItem value="pdf">PDF (.pdf)</SelectItem>
                        <SelectItem value="json">JSON (.json)</SelectItem>
                        <SelectItem value="zip">ZIP Archive</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Date Range */}
                  <div className="space-y-2">
                    <Label>Date Range (Optional)</Label>
                    <div className="grid grid-cols-2 gap-2">
                      <Input
                        id="startDate"
                        type="date"
                        placeholder="Start date"
                        value={exportForm.start_date}
                        onChange={(e) => setExportForm(prev => ({ ...prev, start_date: e.target.value }))}
                      />
                      <Input
                        id="endDate"
                        type="date"
                        placeholder="End date"
                        value={exportForm.end_date}
                        onChange={(e) => setExportForm(prev => ({ ...prev, end_date: e.target.value }))}
                      />
                    </div>
                  </div>

                  {/* Department Filter */}
                  {exportForm.data_type === 'employees' && (
                    <div className="space-y-2">
                      <Label htmlFor="department">Department Filter (Optional)</Label>
                      <Select
                        value={exportForm.department_id || "all"}
                        onValueChange={(value) => setExportForm(prev => ({ ...prev, department_id: value }))}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="All departments" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All departments</SelectItem>
                          {departments.map((dept) => (
                            <SelectItem key={dept.department_id} value={dept.department_id.toString()}>
                              {dept.department_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}

                  {/* Export Progress */}
                  {isExporting && (
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm">Export in progress...</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${exportProgress}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-muted-foreground">{exportMessage}</p>
                    </div>
                  )}

                  <DialogFooter>
                    <Button type="submit" disabled={isExporting}>
                      {isExporting ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Exporting...
                        </>
                      ) : (
                        <>
                          <Play className="mr-2 h-4 w-4" />
                          Generate Export
                        </>
                      )}
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Exports</CardTitle>
                <FileArchive className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{totalExports}</div>
                <p className="text-xs text-muted-foreground">All exports</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Records</CardTitle>
                <Database className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{totalRecords}</div>
                <p className="text-xs text-muted-foreground">Records exported</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Completed</CardTitle>
                <CheckCircle className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{completedExports}</div>
                <p className="text-xs text-muted-foreground">Successful exports</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Processing</CardTitle>
                <RefreshCw className="h-4 w-4 text-yellow-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {exportRecords.filter(r => r.status === 'Processing').length}
                </div>
                <p className="text-xs text-muted-foreground">In progress</p>
              </CardContent>
            </Card>
          </div>

          {/* Export Records Table */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Export Records</CardTitle>
                  <CardDescription>
                    View and manage data export records
                  </CardDescription>
                </div>
                <div className="flex space-x-2">
                  <Input
                    placeholder="Search exports..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-64"
                  />
                  <Select
                    value={filters.status || "all"}
                    onValueChange={(value) => setFilters(prev => ({ ...prev, status: value }))}
                  >
                    <SelectTrigger className="w-32">
                      <SelectValue placeholder="Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Status</SelectItem>
                      <SelectItem value="Completed">Completed</SelectItem>
                      <SelectItem value="Processing">Processing</SelectItem>
                      <SelectItem value="Failed">Failed</SelectItem>
                      <SelectItem value="Scheduled">Scheduled</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select
                    value={filters.type || "all"}
                    onValueChange={(value) => setFilters(prev => ({ ...prev, type: value }))}
                  >
                    <SelectTrigger className="w-32">
                      <SelectValue placeholder="Type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      <SelectItem value="Employee List">Employees</SelectItem>
                      <SelectItem value="Payroll Summary">Payroll</SelectItem>
                      <SelectItem value="Overtime Report">Overtime</SelectItem>
                      <SelectItem value="Activity Log">Activities</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type</TableHead>
                      <TableHead>Format</TableHead>
                      <TableHead>Records</TableHead>
                      <TableHead>Generated By</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredRecords.length > 0 ? (
                      filteredRecords.map((record) => (
                        <TableRow key={record.export_id}>
                          <TableCell>
                            <div className="flex items-center space-x-2">
                              <FileText className="h-4 w-4" />
                              <span>{record.export_type}</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{record.format}</Badge>
                          </TableCell>
                          <TableCell>
                            <span className="text-sm font-medium">{record.record_count}</span>
                          </TableCell>
                          <TableCell>{record.generated_by}</TableCell>
                          <TableCell>{formatDate(record.generated_date)}</TableCell>
                          <TableCell>{getStatusBadge(record.status)}</TableCell>
                          <TableCell>
                            <div className="flex items-center space-x-2">
                              {record.status === 'Completed' && record.file_url && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => record.file_url && handleDownload(record.file_url, `${record.export_type}.${record.format.toLowerCase()}`)}
                                >
                                  <Download className="h-4 w-4" />
                                </Button>
                              )}
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setSelectedRecord(record)}
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDelete(record.export_id)}
                                className="text-red-600 hover:text-red-700"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-6">
                          No export records found
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          {/* Export History Section */}
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>Export History</CardTitle>
                  <CardDescription>
                    Recent export activities and file downloads
                  </CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={fetchExportData}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {exportHistory.map((record) => (
                  <div key={record.export_id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="p-2 bg-blue-100 rounded-lg">
                        <FileSpreadsheet className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <h4 className="font-medium">{record.type}</h4>
                        <p className="text-sm text-muted-foreground">
                          {record.format} • {record.records} records • {record.file_size}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <p className="text-sm font-medium">{record.generated_by}</p>
                        <p className="text-xs text-muted-foreground">{formatDate(record.generated_date)}</p>
                      </div>
                      <div className="flex items-center space-x-2">
                        {record.status === 'Completed' && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDownload(`/export/${record.type}`, `${record.type}.${record.format.toLowerCase()}`)}
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                        )}
                        <Badge variant={record.status === 'Completed' ? 'default' : 'secondary'}>
                          {record.status}
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* View Export Dialog */}
          <Dialog open={!!selectedRecord} onOpenChange={() => setSelectedRecord(null)}>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Export Details</DialogTitle>
                <DialogDescription>
                  View detailed information about the export.
                </DialogDescription>
              </DialogHeader>
              {selectedRecord && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">Export Type</Label>
                      <p className="text-sm">{selectedRecord.export_type}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">Format</Label>
                      <p className="text-sm">{selectedRecord.format}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">Record Count</Label>
                      <p className="text-sm">{selectedRecord.record_count} records</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">Generated By</Label>
                      <p className="text-sm">{selectedRecord.generated_by}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">Generated Date</Label>
                      <p className="text-sm">{formatDate(selectedRecord.generated_date)}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">Status</Label>
                      <div>{getStatusBadge(selectedRecord.status)}</div>
                    </div>
                  </div>
                  {selectedRecord.file_url && (
                    <div className="pt-4 border-t">
                      <Button 
                        className="w-full" 
                        onClick={() => selectedRecord.file_url && handleDownload(selectedRecord.file_url, `${selectedRecord.export_type}.${selectedRecord.format.toLowerCase()}`)}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download File
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </DialogContent>
          </Dialog>
        </div>
      </Layout>
    </ProtectedRoute>
  )
}