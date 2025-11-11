'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { LayoutWrapper } from '@/components/layout'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  User,
  Mail,
  Phone,
  Building,
  Calendar,
  Shield,
  Bell,
  Monitor,
  Save,
  AlertCircle
} from 'lucide-react'

interface SettingsData {
  profile: {
    full_name: string
    email: string
    phone: string
    department: string
    join_date: string
  }
  preferences: {
    theme: 'light' | 'dark' | 'system'
    notifications: boolean
    email_notifications: boolean
  }
  security: {
    two_factor: boolean
    last_login: string
    active_sessions: number
  }
}

export default function SettingsPage() {
  const { user } = useAuth()
  const [settings, setSettings] = useState<SettingsData>({
    profile: {
      full_name: user?.full_name || '',
      email: user?.email || '',
      phone: user?.phone || '',
      department: user?.department || '',
      join_date: user?.join_date || ''
    },
    preferences: {
      theme: 'system',
      notifications: true,
      email_notifications: true
    },
    security: {
      two_factor: false,
      last_login: '2025-01-25 09:30:15',
      active_sessions: 3
    }
  })
  const [isLoading, setIsLoading] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle')

  const handleProfileChange = (field: keyof SettingsData['profile'], value: string) => {
    setSettings(prev => ({
      ...prev,
      profile: {
        ...prev.profile,
        [field]: value
      }
    }))
  }

  const handlePreferenceChange = (field: keyof SettingsData['preferences'], value: any) => {
    setSettings(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        [field]: value
      }
    }))
  }

  const handleSave = async () => {
    setIsLoading(true)
    setSaveStatus('saving')
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500))
      setSaveStatus('success')
      setTimeout(() => setSaveStatus('idle'), 3000)
    } catch (error) {
      setSaveStatus('error')
      setTimeout(() => setSaveStatus('idle'), 3000)
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusMessage = () => {
    switch (saveStatus) {
      case 'saving':
        return { message: 'Saving changes...', type: 'info' as const }
      case 'success':
        return { message: 'Changes saved successfully!', type: 'success' as const }
      case 'error':
        return { message: 'Failed to save changes. Please try again.', type: 'error' as const }
      default:
        return null
    }
  }

  const statusInfo = getStatusMessage()

  return (
    <ProtectedRoute>
      <LayoutWrapper>
        <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">Manage your account settings and preferences</p>
        </div>

        {/* Status Message */}
        {statusInfo && (
          <div className={`p-4 rounded-md ${
            statusInfo.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' :
            statusInfo.type === 'error' ? 'bg-red-50 text-red-800 border border-red-200' :
            'bg-blue-50 text-blue-800 border border-blue-200'
          }`}>
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-4 w-4" />
              <span className="font-medium">{statusInfo.message}</span>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Profile Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <User className="h-5 w-5" />
                <span>Profile Settings</span>
              </CardTitle>
              <CardDescription>
                Update your personal information
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="full_name">Full Name</Label>
                <Input
                  id="full_name"
                  value={settings.profile.full_name}
                  onChange={(e) => handleProfileChange('full_name', e.target.value)}
                  placeholder="Enter your full name"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={settings.profile.email}
                  onChange={(e) => handleProfileChange('email', e.target.value)}
                  placeholder="Enter your email"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="phone">Phone</Label>
                <Input
                  id="phone"
                  type="tel"
                  value={settings.profile.phone}
                  onChange={(e) => handleProfileChange('phone', e.target.value)}
                  placeholder="Enter your phone number"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="department">Department</Label>
                <Input
                  id="department"
                  value={settings.profile.department}
                  onChange={(e) => handleProfileChange('department', e.target.value)}
                  placeholder="Enter your department"
                />
              </div>
            </CardContent>
          </Card>

          {/* Preferences */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Monitor className="h-5 w-5" />
                <span>Preferences</span>
              </CardTitle>
              <CardDescription>
                Customize your experience
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Theme</Label>
                <div className="flex space-x-2">
                  {['light', 'dark', 'system'].map((theme) => (
                    <Button
                      key={theme}
                      variant={settings.preferences.theme === theme ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => handlePreferenceChange('theme', theme)}
                    >
                      {theme.charAt(0).toUpperCase() + theme.slice(1)}
                    </Button>
                  ))}
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Bell className="h-4 w-4" />
                  <Label htmlFor="notifications">Push Notifications</Label>
                </div>
                <Button
                  variant={settings.preferences.notifications ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handlePreferenceChange('notifications', !settings.preferences.notifications)}
                >
                  {settings.preferences.notifications ? 'Enabled' : 'Disabled'}
                </Button>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Mail className="h-4 w-4" />
                  <Label htmlFor="email_notifications">Email Notifications</Label>
                </div>
                <Button
                  variant={settings.preferences.email_notifications ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handlePreferenceChange('email_notifications', !settings.preferences.email_notifications)}
                >
                  {settings.preferences.email_notifications ? 'Enabled' : 'Disabled'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Security */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Shield className="h-5 w-5" />
                <span>Security</span>
              </CardTitle>
              <CardDescription>
                Manage your security settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Shield className="h-4 w-4" />
                  <span>Two-Factor Authentication</span>
                </div>
                <Button
                  variant={settings.security.two_factor ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handlePreferenceChange('two_factor' as any, !settings.security.two_factor)}
                >
                  {settings.security.two_factor ? 'Enabled' : 'Disabled'}
                </Button>
              </div>
              
              <div className="border-t my-4" />
              
              <div className="space-y-2">
                <Label>Last Login</Label>
                <p className="text-sm text-muted-foreground">{settings.security.last_login}</p>
              </div>
              
              <div className="space-y-2">
                <Label>Active Sessions</Label>
                <Badge variant="secondary">{settings.security.active_sessions} devices</Badge>
              </div>
            </CardContent>
          </Card>

          {/* Account Info */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Building className="h-5 w-5" />
                <span>Account Information</span>
              </CardTitle>
              <CardDescription>
                Your account details
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Username</Label>
                <p className="text-sm font-medium">{user?.username}</p>
              </div>
              
              <div className="space-y-2">
                <Label>Role</Label>
                <Badge variant="outline">{user?.role}</Badge>
              </div>
              
              <div className="space-y-2">
                <Label>Join Date</Label>
                <p className="text-sm text-muted-foreground">
                  {settings.profile.join_date ? new Date(settings.profile.join_date).toLocaleDateString() : 'Not provided'}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <Button onClick={handleSave} disabled={isLoading}>
            <Save className="h-4 w-4 mr-2" />
            {isLoading ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>
      </LayoutWrapper>
    </ProtectedRoute>
  )
}