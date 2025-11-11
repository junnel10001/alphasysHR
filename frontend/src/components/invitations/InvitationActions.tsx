'use client'

import { useState } from 'react'
import { toast } from 'react-hot-toast'
import { format } from 'date-fns'

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { InvitationStatusBadge } from './InvitationStatusBadge'
import { invitationService } from '@/lib/api'
import { Invitation, InvitationStatus } from '@/types/invitation'
import { 
  MoreHorizontal, 
  Eye, 
  Send, 
  X, 
  Copy,
  Calendar,
  User
} from 'lucide-react'

interface InvitationActionsProps {
  invitation: Invitation
  onResend?: (invitationId: number) => void
  onRevoke?: (invitationId: number, reason?: string) => void
  onView?: (invitationId: number) => void
  className?: string
}

export function InvitationActions({
  invitation,
  onResend,
  onRevoke,
  onView,
  className
}: InvitationActionsProps) {
  const [isLoading, setIsLoading] = useState(false)

  const handleResend = async () => {
    if (isLoading) return
    
    try {
      setIsLoading(true)
      await invitationService.resendInvitation({
        invitation_id: invitation.invitation_id,
        expires_days: 7
      })
      toast.success('Invitation resent successfully!')
      onResend?.(invitation.invitation_id)
    } catch (error: any) {
      console.error('Failed to resend invitation:', error)
      const errorMessage = error.response?.data?.detail || 'Failed to resend invitation'
      toast.error(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRevoke = async () => {
    if (isLoading) return
    
    const reason = prompt('Please provide a reason for revoking this invitation:')
    if (reason === null) return // User cancelled
    
    try {
      setIsLoading(true)
      await invitationService.revokeInvitation({
        invitation_id: invitation.invitation_id,
        reason: reason || undefined
      })
      toast.success('Invitation revoked successfully!')
      onRevoke?.(invitation.invitation_id, reason || undefined)
    } catch (error: any) {
      console.error('Failed to revoke invitation:', error)
      const errorMessage = error.response?.data?.detail || 'Failed to revoke invitation'
      toast.error(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCopyLink = () => {
    const invitationLink = `${window.location.origin}/invite/accept?token=${invitation.token}`
    navigator.clipboard.writeText(invitationLink)
    toast.success('Invitation link copied to clipboard!')
  }

  const canResend = invitation.status === InvitationStatus.PENDING || invitation.status === InvitationStatus.EXPIRED
  const canRevoke = invitation.status === InvitationStatus.PENDING
  const canView = true

  return (
    <div className={className}>
      <div className="flex items-center gap-2">
        <InvitationStatusBadge status={invitation.status} />
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0" disabled={isLoading}>
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {canView && (
              <DropdownMenuItem onClick={() => onView?.(invitation.invitation_id)}>
                <Eye className="mr-2 h-4 w-4" />
                View Details
              </DropdownMenuItem>
            )}
            
            {canResend && (
              <DropdownMenuItem onClick={handleResend} disabled={isLoading}>
                <Send className="mr-2 h-4 w-4" />
                {isLoading ? 'Resending...' : 'Resend Invitation'}
              </DropdownMenuItem>
            )}
            
            {canRevoke && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  onClick={handleRevoke} 
                  disabled={isLoading}
                  className="text-red-600"
                >
                  <X className="mr-2 h-4 w-4" />
                  {isLoading ? 'Revoking...' : 'Revoke Invitation'}
                </DropdownMenuItem>
              </>
            )}
            
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleCopyLink}>
              <Copy className="mr-2 h-4 w-4" />
              Copy Invitation Link
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      
      {/* Additional info display */}
      <div className="text-xs text-muted-foreground mt-1 space-y-1">
        <div className="flex items-center gap-1">
          <Calendar className="h-3 w-3" />
          Expires: {format(new Date(invitation.expires_at), 'MMM dd, yyyy')}
        </div>
        
        {invitation.invited_by_user && (
          <div className="flex items-center gap-1">
            <User className="h-3 w-3" />
            By: {invitation.invited_by_user.first_name} {invitation.invited_by_user.last_name}
          </div>
        )}
      </div>
    </div>
  )
}

export default InvitationActions