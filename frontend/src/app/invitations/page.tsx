'use client'

import { useEffect, useState } from 'react'
import { toast } from 'react-hot-toast'

import { LayoutWrapper } from '@/components/layout'
import { InvitationDialog } from '@/components/invitations/InvitationDialog'
import { InvitationList } from '@/components/invitations/InvitationList'
import { invitationService } from '@/lib/api'
import { Invitation, InvitationStatistics } from '@/types/invitation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { 
  Mail, 
  Users, 
  CheckCircle, 
  Clock, 
  XCircle, 
  TrendingUp,
  Plus
} from 'lucide-react'

export default function InvitationsPage() {
  const [invitations, setInvitations] = useState<Invitation[]>([])
  const [statistics, setStatistics] = useState<InvitationStatistics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  // Load invitations and statistics
  const loadData = async () => {
    try {
      setIsLoading(true)
      const [invitationsData, statisticsData] = await Promise.all([
        invitationService.getInvitations(),
        invitationService.getInvitationStatistics()
      ])
      setInvitations(invitationsData.invitations || [])
      setStatistics(statisticsData)
    } catch (error: any) {
      console.error('Failed to load invitations:', error)
      const errorMessage = error.response?.data?.detail || 'Failed to load invitations'
      toast.error(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleInvitationAction = async (action: string, invitation: Invitation) => {
    switch (action) {
      case 'resend':
      case 'revoke':
        // Reload data after action
        await loadData()
        break
      case 'view':
        // TODO: Implement view details modal
        toast('View details functionality coming soon')
        break
      default:
        break
    }
  }

  const handleInvitationSuccess = (newInvitation: Invitation) => {
    setInvitations(prev => [newInvitation, ...prev])
    loadData() // Reload to get updated statistics
  }

  const handleCleanupExpired = async () => {
    if (!confirm('Are you sure you want to clean up expired invitations? This will mark all pending invitations that have expired as expired.')) {
      return
    }

    try {
      await invitationService.cleanupExpiredInvitations()
      toast.success('Expired invitations cleaned up successfully!')
      loadData()
    } catch (error: any) {
      console.error('Failed to cleanup expired invitations:', error)
      const errorMessage = error.response?.data?.detail || 'Failed to cleanup expired invitations'
      toast.error(errorMessage)
    }
  }

  if (isLoading && !invitations.length) {
    return (
      <LayoutWrapper>
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
        </div>
      </LayoutWrapper>
    )
  }

  return (
    <LayoutWrapper>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Invitations</h1>
            <p className="text-muted-foreground">
              Manage user invitations, track their status, and monitor acceptance rates.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              onClick={handleCleanupExpired}
              disabled={isLoading}
            >
              <Clock className="h-4 w-4 mr-2" />
              Cleanup Expired
            </Button>
            <Button onClick={() => setIsDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Send Invitation
            </Button>
          </div>
        </div>

        {/* Statistics Cards */}
        {statistics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Invitations</CardTitle>
                <Mail className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.total_invitations}</div>
                <p className="text-xs text-muted-foreground">
                  All time invitations sent
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Pending</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">{statistics.pending_invitations}</div>
                <p className="text-xs text-muted-foreground">
                  Awaiting acceptance
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Accepted</CardTitle>
                <CheckCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">{statistics.accepted_invitations}</div>
                <p className="text-xs text-muted-foreground">
                  Successfully registered
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Acceptance Rate</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {statistics.acceptance_rate.toFixed(1)}%
                </div>
                <p className="text-xs text-muted-foreground">
                  {statistics.invitations_this_month} this month
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Additional Statistics */}
        {statistics && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Expired Invitations</CardTitle>
                <CardDescription>Invitations that have passed their expiration date</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  <XCircle className="h-8 w-8 text-yellow-600" />
                  <div>
                    <div className="text-2xl font-bold text-yellow-600">{statistics.expired_invitations}</div>
                    <p className="text-sm text-muted-foreground">
                      {statistics.expired_invitations > 0 && (
                        <Button 
                          variant="link" 
                          className="p-0 h-auto text-sm"
                          onClick={handleCleanupExpired}
                        >
                          Mark as expired
                        </Button>
                      )}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Revoked Invitations</CardTitle>
                <CardDescription>Invitations that were manually revoked</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  <XCircle className="h-8 w-8 text-red-600" />
                  <div>
                    <div className="text-2xl font-bold text-red-600">{statistics.revoked_invitations}</div>
                    <p className="text-sm text-muted-foreground">
                      Cancelled by administrators
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">This Month</CardTitle>
                <CardDescription>Invitations sent in the current month</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  <Users className="h-8 w-8 text-blue-600" />
                  <div>
                    <div className="text-2xl font-bold text-blue-600">{statistics.invitations_this_month}</div>
                    <p className="text-sm text-muted-foreground">
                      New invitations this month
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Invitations List */}
        <InvitationList
          invitations={invitations}
          loading={isLoading}
          onRefresh={loadData}
          onInvitationAction={handleInvitationAction}
        />

        {/* Invitation Dialog */}
        <InvitationDialog
          open={isDialogOpen}
          onOpenChange={setIsDialogOpen}
          onSuccess={handleInvitationSuccess}
        />
      </div>
    </LayoutWrapper>
  )
}