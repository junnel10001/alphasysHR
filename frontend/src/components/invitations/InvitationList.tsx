'use client'

import { useState } from 'react'
import { format } from 'date-fns'
import { toast } from 'react-hot-toast'

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { InvitationActions } from './InvitationActions'
import { InvitationStatusBadge } from './InvitationStatusBadge'
import { invitationService } from '@/lib/api'
import { Invitation, InvitationStatus } from '@/types/invitation'
import { Search, RefreshCw, Users, Mail, Calendar } from 'lucide-react'

interface InvitationListProps {
  invitations: Invitation[]
  loading?: boolean
  onRefresh?: () => void
  onInvitationAction?: (action: string, invitation: Invitation) => void
  className?: string
}

export function InvitationList({
  invitations,
  loading = false,
  onRefresh,
  onInvitationAction,
  className
}: InvitationListProps) {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Filter invitations based on search and status
  const filteredInvitations = invitations.filter(invitation => {
    const matchesSearch = !search || 
      invitation.email.toLowerCase().includes(search.toLowerCase()) ||
      invitation.invited_by_user?.first_name?.toLowerCase().includes(search.toLowerCase()) ||
      invitation.invited_by_user?.last_name?.toLowerCase().includes(search.toLowerCase()) ||
      invitation.role?.role_name?.toLowerCase().includes(search.toLowerCase()) ||
      invitation.department?.department_name?.toLowerCase().includes(search.toLowerCase())
    
    const matchesStatus = statusFilter === 'all' || invitation.status === statusFilter
    
    return matchesSearch && matchesStatus
  })

  const handleRefresh = async () => {
    if (isRefreshing) return
    
    try {
      setIsRefreshing(true)
      onRefresh?.()
    } catch (error) {
      console.error('Failed to refresh invitations:', error)
      toast.error('Failed to refresh invitations')
    } finally {
      setIsRefreshing(false)
    }
  }

  const handleInvitationAction = (action: string, invitation: Invitation) => {
    onInvitationAction?.(action, invitation)
  }

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM dd, yyyy HH:mm')
    } catch {
      return 'Invalid date'
    }
  }

  const isExpired = (invitation: Invitation) => {
    return new Date(invitation.expires_at) < new Date() && invitation.status === InvitationStatus.PENDING
  }

  return (
    <div className={className}>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5" />
                Invitations
              </CardTitle>
              <CardDescription>
                Manage user invitations and track their status
              </CardDescription>
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleRefresh}
              disabled={loading || isRefreshing}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="flex items-center flex-1">
              <Search className="h-4 w-4 mr-2 text-muted-foreground" />
              <Input
                placeholder="Search by email, name, role, department..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="max-w-sm"
              />
            </div>
            
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full sm:w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value={InvitationStatus.PENDING}>Pending</SelectItem>
                <SelectItem value={InvitationStatus.ACCEPTED}>Accepted</SelectItem>
                <SelectItem value={InvitationStatus.EXPIRED}>Expired</SelectItem>
                <SelectItem value={InvitationStatus.REVOKED}>Revoked</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Statistics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg">
              <Users className="h-5 w-5 text-blue-600" />
              <div>
                <p className="text-sm font-medium text-blue-900">
                  {invitations.filter(i => i.status === InvitationStatus.PENDING).length}
                </p>
                <p className="text-xs text-blue-700">Pending</p>
              </div>
            </div>
            <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg">
              <Users className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-sm font-medium text-green-900">
                  {invitations.filter(i => i.status === InvitationStatus.ACCEPTED).length}
                </p>
                <p className="text-xs text-green-700">Accepted</p>
              </div>
            </div>
            <div className="flex items-center gap-2 p-3 bg-yellow-50 rounded-lg">
              <Calendar className="h-5 w-5 text-yellow-600" />
              <div>
                <p className="text-sm font-medium text-yellow-900">
                  {invitations.filter(i => i.status === InvitationStatus.EXPIRED).length}
                </p>
                <p className="text-xs text-yellow-700">Expired</p>
              </div>
            </div>
            <div className="flex items-center gap-2 p-3 bg-red-50 rounded-lg">
              <Users className="h-5 w-5 text-red-600" />
              <div>
                <p className="text-sm font-medium text-red-900">
                  {invitations.filter(i => i.status === InvitationStatus.REVOKED).length}
                </p>
                <p className="text-xs text-red-700">Revoked</p>
              </div>
            </div>
          </div>

          {/* Table */}
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : filteredInvitations.length === 0 ? (
            <div className="text-center py-8">
              <Mail className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No invitations found</h3>
              <p className="text-muted-foreground">
                {search || statusFilter !== 'all' 
                  ? 'No invitations match your current filters.'
                  : 'No invitations have been sent yet.'
                }
              </p>
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Email</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Department</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Expires</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredInvitations.map((invitation) => (
                    <TableRow key={invitation.invitation_id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{invitation.email}</p>
                          {invitation.employee_profile && (
                            <p className="text-sm text-muted-foreground">
                              {invitation.employee_profile.first_name} {invitation.employee_profile.last_name}
                            </p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {invitation.role?.role_name || 'Unknown'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {invitation.department?.department_name || '-'}
                      </TableCell>
                      <TableCell>
                        <InvitationStatusBadge status={invitation.status} />
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {formatDate(invitation.created_at)}
                          {invitation.invited_by_user && (
                            <p className="text-muted-foreground">
                              by {invitation.invited_by_user.first_name} {invitation.invited_by_user.last_name}
                            </p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {formatDate(invitation.expires_at)}
                          {isExpired(invitation) && (
                            <Badge variant="destructive" className="mt-1">
                              Expired
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <InvitationActions
                          invitation={invitation}
                          onView={(id) => handleInvitationAction('view', invitation)}
                          onResend={(id) => handleInvitationAction('resend', invitation)}
                          onRevoke={(id, reason) => handleInvitationAction('revoke', invitation)}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default InvitationList