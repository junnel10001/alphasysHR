'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { LayoutWrapper, PermissionProtectedRoute } from '@/components'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Monitor,
  Database,
  Cpu,
  HardDrive,
  Activity,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  XCircle
} from 'lucide-react'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"

interface HealthCheck {
  status: 'healthy' | 'warning' | 'critical' | 'unknown'
  message: string
  lastChecked: string
}

interface SystemInfo {
  system: {
    platform: string
    platform_version: string
    architecture: string
    processor: string
    python_version: string
  }
  database: {
    users_total: number
    users_active: number
    departments: number
    roles: number
    offices: number
    leave_types: number
  }
  performance: {
    cpu_usage: number
    memory: {
      total: number
      available: number
      used: number
      percent: number
    }
    disk: {
      total: number
      used: number
      free: number
      percent: number
    }
  }
  versions: {
    fastapi: string
    sqlalchemy: string
    python: string
    app_version: string
  }
  environment: {
    debug: boolean
    environment: string
    database_url: string
  }
}

export default function SystemHealthPage() {
  const { user } = useAuth()
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null)
  const [healthChecks, setHealthChecks] = useState<HealthCheck[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    fetchSystemInfo()
    fetchHealthChecks()
  }, [])

  const fetchSystemInfo = async () => {
    try {
      // Mock data - replace with actual API call
      const mockSystemInfo: SystemInfo = {
        system: {
          platform: 'Linux',
          platform_version: '5.15.0-76-generic',
          architecture: 'x86_64',
          processor: 'Intel(R) Core(TM) i7-9700K CPU @ 3.60GHz',
          python_version: '3.11.5'
        },
        database: {
          users_total: 45,
          users_active: 42,
          departments: 5,
          roles: 8,
          offices: 4,
          leave_types: 6
        },
        performance: {
          cpu_usage: 15.2,
          memory: {
            total: 16777216000,
            available: 8589934592,
            used: 8187281408,
            percent: 48.8
          },
          disk: {
            total: 500107869184,
            used: 245683097600,
            free: 254424771584,
            percent: 49.1
          }
        },
        versions: {
          fastapi: '0.104.1',
          sqlalchemy: '2.0.23',
          python: '3.11.5',
          app_version: '1.0.0'
        },
        environment: {
          debug: false,
          environment: 'production',
          database_url: 'configured'
        }
      }
      setSystemInfo(mockSystemInfo)
    } catch (error) {
      console.error('Error fetching system info:', error)
    }
  }

  const fetchHealthChecks = async () => {
    try {
      // Mock data - replace with actual API call
      const mockHealthChecks: HealthCheck[] = [
        {
          status: 'healthy',
          message: 'Database connection successful',
          lastChecked: new Date().toISOString()
        },
        {
          status: 'healthy',
          message: 'Memory usage: 48.8%',
          lastChecked: new Date().toISOString()
        },
        {
          status: 'warning',
          message: 'Disk usage: 49.1%',
          lastChecked: new Date().toISOString()
        },
        {
          status: 'healthy',
          message: 'API endpoints responding normally',
          lastChecked: new Date().toISOString()
        }
      ]
      setHealthChecks(mockHealthChecks)
    } catch (error) {
      console.error('Error fetching health checks:', error)
    }
  }

  const refreshSystemInfo = async () => {
    setIsLoading(true)
    await fetchSystemInfo()
    await fetchHealthChecks()
    setIsLoading(false)
  }

  const getHealthStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />
      case 'critical':
        return <XCircle className="h-4 w-4 text-red-600" />
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-600" />
    }
  }

  const getHealthStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'default'
      case 'warning':
        return 'secondary'
      case 'critical':
        return 'destructive'
      default:
        return 'outline'
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const m = k * 1024
    const g = m * 1024
    if (bytes < k) return bytes + ' Bytes'
    if (bytes < m) return (bytes / k).toFixed(1) + ' KB'
    if (bytes < g) return (bytes / m).toFixed(1) + ' MB'
    return (bytes / g).toFixed(1) + ' GB'
  }


  return (
    <PermissionProtectedRoute requiredPermission="system_config">
      <LayoutWrapper>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">System Status</h1>
            <p className="text-muted-foreground">Monitor system health and performance</p>
          </div>
          <Button onClick={refreshSystemInfo} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="health">Health Checks</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="system">System Info</TabsTrigger>
            <TabsTrigger value="environment">Environment</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">System Status</CardTitle>
                  <Monitor className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="flex items-center space-x-2">
                    {getHealthStatusIcon('healthy')}
                    <span className="text-2xl font-bold text-green-600">Healthy</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Active Users</CardTitle>
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{systemInfo.database.users_active}</div>
                  <p className="text-xs text-muted-foreground">of {systemInfo.database.users_total} total</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
                  <Cpu className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{systemInfo.performance.cpu_usage}%</div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                    <div 
                      className={`h-2 rounded-full ${
                        systemInfo.performance.cpu_usage > 80 ? 'bg-red-600' :
                        systemInfo.performance.cpu_usage > 60 ? 'bg-yellow-600' : 'bg-green-600'
                      }`}
                      style={{ width: `${Math.min(systemInfo.performance.cpu_usage, 100)}%` }}
                    ></div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
                  <Database className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{systemInfo.performance.memory.percent}%</div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                    <div 
                      className={`h-2 rounded-full ${
                        systemInfo.performance.memory.percent > 80 ? 'bg-red-600' :
                        systemInfo.performance.memory.percent > 60 ? 'bg-yellow-600' : 'bg-green-600'
                      }`}
                      style={{ width: `${Math.min(systemInfo.performance.memory.percent, 100)}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {formatBytes(systemInfo.performance.memory.used)} of {formatBytes(systemInfo.performance.memory.total)}
                  </p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="health" className="space-y-4">
            {healthChecks.map((check, index) => (
              <Card key={index}>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    {getHealthStatusIcon(check.status)}
                    <span>Health Check</span>
                  </CardTitle>
                  <CardDescription>System component health status</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="font-medium">{check.message}</p>
                      <p className="text-sm text-muted-foreground">
                        Last checked: {new Date(check.lastChecked).toLocaleString()}
                      </p>
                    </div>
                    <Badge variant={getHealthStatusBadgeVariant(check.status)}>
                      {check.status.toUpperCase()}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          <TabsContent value="performance" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Cpu className="h-5 w-5" />
                    <span>CPU Usage</span>
                  </CardTitle>
                  <CardDescription>Current processor utilization</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{systemInfo.performance.cpu_usage}%</div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                    <div 
                      className={`h-2 rounded-full ${
                        systemInfo.performance.cpu_usage > 80 ? 'bg-red-600' :
                        systemInfo.performance.cpu_usage > 60 ? 'bg-yellow-600' : 'bg-green-600'
                      }`}
                      style={{ width: `${Math.min(systemInfo.performance.cpu_usage, 100)}%` }}
                    ></div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Database className="h-5 w-5" />
                    <span>Memory Usage</span>
                  </CardTitle>
                  <CardDescription>RAM utilization</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{systemInfo.performance.memory.percent}%</div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                    <div 
                      className={`h-2 rounded-full ${
                        systemInfo.performance.memory.percent > 80 ? 'bg-red-600' :
                        systemInfo.performance.memory.percent > 60 ? 'bg-yellow-600' : 'bg-green-600'
                      }`}
                      style={{ width: `${Math.min(systemInfo.performance.memory.percent, 100)}%` }}
                    ></div>
                  </div>
                  <div className="text-sm text-muted-foreground mt-2">
                    <div>{formatBytes(systemInfo.performance.memory.used)} used</div>
                    <div>{formatBytes(systemInfo.performance.memory.total)} total</div>
                    <div>{formatBytes(systemInfo.performance.memory.available)} available</div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <HardDrive className="h-5 w-5" />
                    <span>Disk Usage</span>
                  </CardTitle>
                  <CardDescription>Storage utilization</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{systemInfo.performance.disk.percent}%</div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                    <div 
                      className={`h-2 rounded-full ${
                        systemInfo.performance.disk.percent > 80 ? 'bg-red-600' :
                        systemInfo.performance.disk.percent > 60 ? 'bg-yellow-600' : 'bg-green-600'
                      }`}
                      style={{ width: `${Math.min(systemInfo.performance.disk.percent, 100)}%` }}
                    ></div>
                  </div>
                  <div className="text-sm text-muted-foreground mt-2">
                    <div>{formatBytes(systemInfo.performance.disk.used)} used</div>
                    <div>{formatBytes(systemInfo.performance.disk.total)} total</div>
                    <div>{formatBytes(systemInfo.performance.disk.free)} available</div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="system" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>System Information</CardTitle>
                  <CardDescription>Operating system and platform details</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Platform:</span>
                    <span className="text-sm">{systemInfo.system.platform}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Version:</span>
                    <span className="text-sm">{systemInfo.system.platform_version}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Architecture:</span>
                    <span className="text-sm">{systemInfo.system.architecture}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Processor:</span>
                    <span className="text-sm text-right">{systemInfo.system.processor}</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Version Information</CardTitle>
                  <CardDescription>Application and dependency versions</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">App Version:</span>
                    <span className="text-sm">{systemInfo.versions.app_version}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">FastAPI:</span>
                    <span className="text-sm">{systemInfo.versions.fastapi}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">SQLAlchemy:</span>
                    <span className="text-sm">{systemInfo.versions.sqlalchemy}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Python:</span>
                    <span className="text-sm">{systemInfo.versions.python}</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="environment" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Environment Settings</CardTitle>
                  <CardDescription>Current environment configuration</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Environment:</span>
                    <Badge variant={systemInfo.environment.environment === 'production' ? 'default' : 'secondary'}>
                      {systemInfo.environment.environment}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Debug Mode:</span>
                    <Badge variant={systemInfo.environment.debug ? 'destructive' : 'default'}>
                      {systemInfo.environment.debug ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Database:</span>
                    <Badge variant="outline">
                      {systemInfo.environment.database_url}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
      </LayoutWrapper>
    </PermissionProtectedRoute>
  )
}