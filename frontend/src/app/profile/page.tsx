'use client'

import { useAuth } from '@/contexts/AuthContext'
import { LayoutWrapper } from '@/components/layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { PageTemplate, PageGrid } from '@/components/layout'
import { User, Mail, Phone, Building, Calendar } from 'lucide-react'

export default function ProfilePage() {
  const { user } = useAuth()

  return (
    <LayoutWrapper>
      <PageTemplate
        title="My Profile"
        description="Manage your personal information"
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <User className="h-5 w-5" />
              <span>Personal Information</span>
            </CardTitle>
            <CardDescription>
              Your account details and information
            </CardDescription>
          </CardHeader>
          <CardContent>
            <PageGrid cols={2} gap="lg">
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">Full Name</label>
                  <p className="text-lg font-semibold">{user?.full_name}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Email</label>
                  <p className="text-lg font-semibold flex items-center">
                    <Mail className="h-4 w-4 mr-2" />
                    {user?.email}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Phone</label>
                  <p className="text-lg font-semibold flex items-center">
                    <Phone className="h-4 w-4 mr-2" />
                    {user?.phone || 'Not provided'}
                  </p>
                </div>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">Role</label>
                  <Badge variant="secondary" className="mt-1">
                    {user?.role}
                  </Badge>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Department</label>
                  <p className="text-lg font-semibold flex items-center">
                    <Building className="h-4 w-4 mr-2" />
                    {user?.department || 'Not assigned'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Join Date</label>
                  <p className="text-lg font-semibold flex items-center">
                    <Calendar className="h-4 w-4 mr-2" />
                    {user?.join_date ? new Date(user.join_date).toLocaleDateString() : 'Not provided'}
                  </p>
                </div>
              </div>
            </PageGrid>
            <div className="mt-6">
              <Button>Edit Profile</Button>
            </div>
          </CardContent>
        </Card>
      </PageTemplate>
    </LayoutWrapper>
  )
}