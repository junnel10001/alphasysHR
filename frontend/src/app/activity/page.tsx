'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { LayoutWrapper } from '@/components/layout'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
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
  Activity,
  Clock,
  User,
  AlertCircle,
  CheckCircle,
  XCircle,
  FileText,
  Eye,
  Download
} from 'lucide-react'
import { format } from 'date-fns'

interface ActivityLog {
  id: number
  user_id: number
  action: string
  entity: string
  entity_id: number
  details: string
  ip_address: string
  timestamp: string
  status: 'success' | 'failed' | 'pending'
}

export default function ActivityPage() {
  const { user } = useAuth()
  const [activityLogs, setActivityLogs] = useState<ActivityLog[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchActivityLogs()
  }, [])

  const fetchActivityLogs = async () => {
    try {
      setIsLoading(true)
      // Mock data for demonstration
      const mockLogs: ActivityLog[] = [
        {
          id: 1,
          user_id: user?.id || 1,
          action: 'login',
          entity: 'Authentication',
          entity_id: 1,
          details: 'User logged in successfully',
          ip_address: '192.168.1.100',
          timestamp: '2025-01-25 09:30:15',
          status: 'success'
        },
        {
          id: 2,
          user_id: user?.id || 1,
          action: 'create',
          entity: 'Employee',
          entity_id: 2,
          details: 'Created new employee record',
          ip_address: '192.168.1.100',
          timestamp: '2025-01-25 10:15:22',
          status: 'success'
        },
        {
          id: 3,
          user_id: user?.id || 1,
          action: 'update',
          entity: 'Attendance',
          entity_id: 3,
          details: 'Updated attendance record',
          ip_address: '192.168.1.100',
          timestamp: '2025-01-25 11:20:45',
          status: 'success'
        },
        {
          id: 4,
          user_id: user?.id || 1,
          action: 'delete',
          entity: 'Leave',
          entity_id: 4,
          details: 'Attempted to delete leave record',
          ip_address: '192.168.1.100',
          timestamp: '2025-01-25 14:05:33',
          status: 'failed'
        },
        {
          id: 5,
          user_id: user?.id || 1,
          action: 'export',
          entity: 'Payroll',
          entity_id: 5,
          details: 'Exported payroll report',
          ip_address: '192.168.1.100',
          timestamp: '2025-01-25 15:30:10',
          status: 'success'
        }
      ]
      setActivityLogs(mockLogs)
    } catch (error) {
      console.error('Error fetching activity logs:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      'success': { label: 'Success', color: 'bg-green-100 text-green-800', icon: CheckCircle },
      'failed': { label: 'Failed', color: 'bg-red-100 text-red-800', icon: XCircle },
      'pending': { label: 'Pending', color: 'bg-yellow-100 text-yellow-800', icon: Clock }
    }
    
    const config = statusConfig[status as keyof typeof statusConfig]
    if (!config) return <Badge variant="secondary">{status}</Badge>
    
    return (
      <Badge className={config.color}>
        <config.icon className="h-3 w-3 mr-1" />
        {config.label}
      </Badge>
    )
  }

  const getActionIcon = (action: string) => {
    const actionConfig = {
      'login': { icon: User, color: 'text-blue-600' },
      'create': { icon: FileText, color: 'text-green-600' },
      'update': { icon: FileText, color: 'text-yellow-600' },
      'delete': { icon: AlertCircle, color: 'text-red-600' },
      'export': { icon: Download, color: 'text-purple-600' },
      'view': { icon: Eye, color: 'text-gray-600' }
    }
    
    const config = actionConfig[action as keyof typeof actionConfig] || { icon: Activity, color: 'text-gray-600' }
    return <config.icon className={`h-4 w-4 ${config.color}`} />
  }

  const formatDateTime = (dateString: string) => {
    return format(new Date(dateString), 'MMM dd, yyyy HH:mm')
  }

  const getActionDescription = (action: string) => {
    const descriptions = {
      'login': 'User authentication',
      'create': 'Created new record',
      'update': 'Modified existing record',
      'delete': 'Removed record',
      'export': 'Data export',
      'view': 'Viewed data',
      'logout': 'User logout'
    }
    return descriptions[action as keyof typeof descriptions] || action
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return (
    <ProtectedRoute>
      <LayoutWrapper>
        <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Activity Logs</h1>
          <p className="text-muted-foreground">View system activity and user actions</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Activities</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{activityLogs.length}</div>
              <p className="text-xs text-muted-foreground">All activities</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Success</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {activityLogs.filter(r => r.status === 'success').length}
              </div>
              <p className="text-xs text-muted-foreground">Successful actions</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Failed</CardTitle>
              <AlertCircle className="h-4 w-4 text-red-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {activityLogs.filter(r => r.status === 'failed').length}
              </div>
              <p className="text-xs text-muted-foreground">Failed actions</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Today</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {activityLogs.filter(log => {
                  const logDate = new Date(log.timestamp)
                  const today = new Date()
                  return logDate.toDateString() === today.toDateString()
                }).length}
              </div>
              <p className="text-xs text-muted-foreground">Recent activities</p>
            </CardContent>
          </Card>
        </div>

        {/* Activity Table */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>
              System activity logs and user actions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Time</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Entity</TableHead>
                    <TableHead>Details</TableHead>
                    <TableHead>IP Address</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {activityLogs.length > 0 ? (
                    activityLogs.map((log) => (
                      <TableRow key={log.id}>
                        <TableCell className="font-medium">
                          {formatDateTime(log.timestamp)}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            {getActionIcon(log.action)}
                            <span>{getActionDescription(log.action)}</span>
                          </div>
                        </TableCell>
                        <TableCell className="capitalize">{log.entity}</TableCell>
                        <TableCell className="max-w-xs truncate">{log.details}</TableCell>
                        <TableCell className="font-mono text-sm">{log.ip_address}</TableCell>
                        <TableCell>{getStatusBadge(log.status)}</TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-6">
                        No activity logs found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
      </LayoutWrapper>
    </ProtectedRoute>
  )
}