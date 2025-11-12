'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { LayoutWrapper, PermissionProtectedRoute } from '@/components'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Settings,
  Users,
  Shield,
  Building,
  Calendar,
  Briefcase,
  UserCheck,
  Activity,
  Database,
  Monitor,
  AlertTriangle
} from 'lucide-react'
import {
  systemStatusService,
  departmentService,
  roleService,
  leaveTypesService,
  positionsService,
  employmentStatusesService
} from '@/lib/api'

interface SystemStats {
  departments: number
  roles: number
  offices: number
  leaveTypes: number
  positions: number
  employmentStatuses: number
  activeUsers: number
  systemHealth: 'healthy' | 'warning' | 'error' | 'unhealthy' | 'critical'
}

export default function SystemConfigPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState<SystemStats>({
    departments: 0,
    roles: 0,
    offices: 0,
    leaveTypes: 0,
    positions: 0,
    employmentStatuses: 0,
    activeUsers: 0,
    systemHealth: 'healthy'
  })
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Fetch system statistics from database
    const fetchStats = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // Fetch system info and health status in parallel
        const [systemInfo, healthCheck] = await Promise.all([
          systemStatusService.getSystemInfo(),
          systemStatusService.getHealthCheck()
        ])

        // Fetch all counts in parallel
        const [departments, roles, offices, leaveTypes, positions, employmentStatuses] = await Promise.all([
          departmentService.getDepartments().then(data => data.length || 0).catch(() => 0),
          roleService.getRoles().then(data => data.length || 0).catch(() => 0),
          departmentService.getOffices().then(data => data.length || 0).catch(() => 0),
          leaveTypesService.getLeaveTypes().then(data => data.length || 0).catch(() => 0),
          positionsService.getPositions().then(data => data.length || 0).catch(() => 0),
          employmentStatusesService.getEmploymentStatuses().then(data => data.length || 0).catch(() => 0)
        ])

        // Determine system health from health check
        let systemHealth: 'healthy' | 'warning' | 'error' | 'unhealthy' | 'critical' = 'healthy'
        if (healthCheck.status === 'unhealthy') {
          systemHealth = 'error'
        } else if (healthCheck.status === 'warning') {
          systemHealth = 'warning'
        }

        // Check individual components for more specific health status
        Object.values(healthCheck.checks || {}).forEach((check: any) => {
          if (check.status === 'critical') {
            systemHealth = 'critical'
          } else if (check.status === 'unhealthy' && systemHealth !== 'critical') {
            systemHealth = 'error'
          } else if (check.status === 'warning' && systemHealth === 'healthy') {
            systemHealth = 'warning'
          }
        })

        const realStats: SystemStats = {
          departments,
          roles,
          offices,
          leaveTypes,
          positions,
          employmentStatuses,
          activeUsers: systemInfo.database?.users_active || 0,
          systemHealth
        }

        setStats(realStats)
      } catch (error: any) {
        console.error('Error fetching system stats:', error)
        setError(error.response?.data?.detail || 'Failed to fetch system statistics')
        
        // Set default stats on error
        setStats({
          departments: 0,
          roles: 0,
          offices: 0,
          leaveTypes: 0,
          positions: 0,
          employmentStatuses: 0,
          activeUsers: 0,
          systemHealth: 'error'
        })
      } finally {
        setIsLoading(false)
      }
    }

    fetchStats()
  }, [])

  const configSections = [
    {
      title: 'System Definitions',
      description: 'Manage system-wide definitions and configurations',
      icon: Database,
      items: [
        { name: 'Departments', href: '/system-config/definitions/departments', count: stats.departments },
        { name: 'Roles & Permissions', href: '/system-config/definitions/roles', count: stats.roles },
        { name: 'Offices', href: '/system-config/definitions/offices', count: stats.offices },
        { name: 'Leave Types', href: '/system-config/definitions/leave-types', count: stats.leaveTypes },
        { name: 'Positions', href: '/system-config/definitions/positions', count: stats.positions },
        { name: 'Employment Status', href: '/system-config/definitions/employment-status', count: stats.employmentStatuses }
      ]
    },
    {
      title: 'User Management',
      description: 'Comprehensive user management with role assignment, deactivation, and more',
      icon: Users,
      items: [
        { name: 'User Management', href: '/system-config/users/', count: null }
      ]
    },
    {
      title: 'System Status',
      description: 'Monitor system health and performance',
      icon: Monitor,
      items: [
        { name: 'System Health', href: '/system-config/status/health', count: stats.systemHealth }
      ]
    }
  ]

  const getHealthBadgeVariant = (health: string) => {
    switch (health) {
      case 'healthy':
        return 'default'
      case 'warning':
        return 'secondary'
      case 'error':
        return 'destructive'
      case 'unhealthy':
        return 'destructive'
      case 'critical':
        return 'destructive'
      default:
        return 'outline'
    }
  }

  const getHealthIcon = (health: string) => {
    switch (health) {
      case 'healthy':
        return <Activity className="h-4 w-4 text-green-500" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'error':
      case 'unhealthy':
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      case 'critical':
        return <AlertTriangle className="h-4 w-4 text-red-600" />
      default:
        return <Monitor className="h-4 w-4 text-gray-500" />
    }
  }


  if (error && stats.systemHealth === 'error') {
    return (
      <LayoutWrapper>
        <div className="min-h-screen flex flex-col items-center justify-center">
          <AlertTriangle className="h-16 w-16 text-red-500 mb-4" />
          <h2 className="text-2xl font-bold mb-2">System Configuration Unavailable</h2>
          <p className="text-muted-foreground text-center max-w-md mb-4">{error}</p>
          <Button onClick={() => window.location.reload()}>
            Try Again
          </Button>
        </div>
      </LayoutWrapper>
    )
  }

  return (
    <PermissionProtectedRoute requiredPermission="system_config">
      <LayoutWrapper>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Configuration</h1>
          <p className="text-muted-foreground">Manage system settings and configurations</p>
        </div>

        {/* Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Users</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.activeUsers}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">System Health</CardTitle>
              {getHealthIcon(stats.systemHealth)}
            </CardHeader>
            <CardContent>
              <Badge variant={getHealthBadgeVariant(stats.systemHealth)}>
                {stats.systemHealth.charAt(0).toUpperCase() + stats.systemHealth.slice(1)}
              </Badge>
              {error && (
                <p className="text-xs text-red-500 mt-2">Some data may be unavailable</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Roles</CardTitle>
              <Shield className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.roles}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Offices</CardTitle>
              <Building className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.offices}</div>
            </CardContent>
          </Card>
        </div>

        {/* Configuration Sections */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {configSections.map((section, index) => (
            <Card key={index} className="h-fit">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <section.icon className="h-5 w-5" />
                  <span>{section.title}</span>
                </CardTitle>
                <CardDescription>{section.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {section.items.map((item, itemIndex) => (
                  <div key={itemIndex} className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent/50 transition-colors">
                    <div className="flex items-center space-x-3">
                      {item.name.includes('Departments') && <Building className="h-4 w-4 text-muted-foreground" />}
                      {item.name.includes('Roles') && <Shield className="h-4 w-4 text-muted-foreground" />}
                      {item.name.includes('Offices') && <Building className="h-4 w-4 text-muted-foreground" />}
                      {item.name.includes('Leave') && <Calendar className="h-4 w-4 text-muted-foreground" />}
                      {item.name.includes('Positions') && <Briefcase className="h-4 w-4 text-muted-foreground" />}
                      {item.name.includes('Employment') && <UserCheck className="h-4 w-4 text-muted-foreground" />}
                      {item.name.includes('User Management') && <Users className="h-4 w-4 text-muted-foreground" />}
                      {item.name.includes('Health') && <Monitor className="h-4 w-4 text-muted-foreground" />}
                      
                      <span className="font-medium">{item.name}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      {item.count !== null && (
                        <Badge variant="secondary" className="text-xs">
                          {typeof item.count === 'string' ? item.count : item.count}
                        </Badge>
                      )}
                      <Button variant="ghost" size="sm" asChild>
                        <a href={item.href}>
                          <Settings className="h-4 w-4" />
                        </a>
                      </Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
      </LayoutWrapper>
    </PermissionProtectedRoute>
  )
}