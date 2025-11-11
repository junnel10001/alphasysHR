'use client'

import { Badge } from '@/components/ui/badge'
import { InvitationStatus, InvitationStatusConfig, InvitationStatusColor } from '@/types/invitation'
import { cn } from '@/lib/utils'
import { Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

interface InvitationStatusBadgeProps {
  status: InvitationStatus
  className?: string
}

// Status configuration for consistent styling and labels
const statusConfig: Record<InvitationStatus, InvitationStatusConfig> = {
  [InvitationStatus.PENDING]: {
    label: 'Pending',
    color: 'default' as InvitationStatusColor,
    icon: Clock
  },
  [InvitationStatus.ACCEPTED]: {
    label: 'Accepted',
    color: 'success' as InvitationStatusColor,
    icon: CheckCircle
  },
  [InvitationStatus.EXPIRED]: {
    label: 'Expired',
    color: 'warning' as InvitationStatusColor,
    icon: AlertCircle
  },
  [InvitationStatus.REVOKED]: {
    label: 'Revoked',
    color: 'destructive' as InvitationStatusColor,
    icon: XCircle
  }
}

// Helper function to get badge variant based on status color
const getBadgeVariant = (color: InvitationStatusColor) => {
  switch (color) {
    case 'success':
      return 'default'
    case 'warning':
      return 'secondary'
    case 'destructive':
      return 'destructive'
    case 'outline':
      return 'outline'
    default:
      return 'default'
  }
}

export function InvitationStatusBadge({ status, className }: InvitationStatusBadgeProps) {
  const config = statusConfig[status]
  const Icon = config.icon
  const variant = getBadgeVariant(config.color)

  return (
    <Badge 
      variant={variant} 
      className={cn(
        'inline-flex items-center gap-1 px-2 py-1 text-xs font-medium',
        {
          'bg-green-100 text-green-800 border-green-200': status === InvitationStatus.ACCEPTED,
          'bg-yellow-100 text-yellow-800 border-yellow-200': status === InvitationStatus.EXPIRED,
          'bg-red-100 text-red-800 border-red-200': status === InvitationStatus.REVOKED,
          'bg-blue-100 text-blue-800 border-blue-200': status === InvitationStatus.PENDING,
        },
        className
      )}
    >
      <Icon className="h-3 w-3" />
      {config.label}
    </Badge>
  )
}

export default InvitationStatusBadge