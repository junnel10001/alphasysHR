'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { PublicLayout } from '@/components/layout'
import { invitationService } from '@/lib/api'
import { Mail, AlertCircle, Lock } from 'lucide-react'
import { toast } from 'react-hot-toast'

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    full_name: '',
    password: '',
    confirmPassword: ''
  })
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isValidatingToken, setIsValidatingToken] = useState(false)
  const [invitationData, setInvitationData] = useState<any>(null)
  const [isInvitationValid, setIsInvitationValid] = useState<boolean | null>(null)
  
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get('token')

  // Validate invitation token if present
  useEffect(() => {
    const validateInvitationToken = async () => {
      if (!token) {
        setIsInvitationValid(false)
        return
      }

      setIsValidatingToken(true)
      try {
        const validation = await invitationService.validateInvitationToken(token)
        if (validation.is_valid && validation.invitation_data) {
          setIsInvitationValid(true)
          setInvitationData(validation.invitation_data)
          setFormData(prev => ({
            ...prev,
            email: validation.invitation_data.email,
            full_name: validation.invitation_data.employee_profile
              ? `${validation.invitation_data.employee_profile.first_name} ${validation.invitation_data.employee_profile.last_name}`
              : ''
          }))
        } else {
          setIsInvitationValid(false)
          toast.error('Invalid or expired invitation token')
        }
      } catch (error: any) {
        console.error('Failed to validate invitation token:', error)
        setIsInvitationValid(false)
        toast.error('Failed to validate invitation token')
      } finally {
        setIsValidatingToken(false)
      }
    }

    validateInvitationToken()
  }, [token])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Don't allow changing email and full_name if using invitation
    if (token && isInvitationValid && (e.target.name === 'email' || e.target.name === 'full_name')) {
      return
    }
    
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      setIsLoading(false)
      return
    }

    try {
      let response
      
      if (token && isInvitationValid) {
        // Use invitation acceptance flow
        const acceptData = {
          token: token,
          username: formData.username,
          password: formData.password,
          confirm_password: formData.confirmPassword,
          first_name: invitationData?.employee_profile?.first_name || formData.full_name.split(' ')[0] || '',
          last_name: invitationData?.employee_profile?.last_name || formData.full_name.split(' ').slice(1).join(' ') || '',
          phone_number: '',
        }
        
        response = await invitationService.acceptInvitation(acceptData)
        
        if (response.success) {
          toast.success('Account created successfully! Redirecting to login...')
          setTimeout(() => {
            router.push('/login')
          }, 2000)
        } else {
          setError(typeof response.message === 'string' ? response.message : 'Failed to create account from invitation')
        }
      } else {
        // Regular registration (shouldn't happen with current requirements, but keeping for fallback)
        response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: formData.username,
            email: formData.email,
            full_name: formData.full_name,
            password: formData.password,
          }),
        })

        if (response.ok) {
          toast.success('Registration successful! Redirecting to login...')
          setTimeout(() => {
            router.push('/login')
          }, 2000)
        } else {
          const data = await response.json()
          setError(data.detail || 'Registration failed')
        }
      }
    } catch (err: any) {
      console.error('Registration error:', err)
      let errorMessage = 'An error occurred during registration'
      
      // Handle different error response structures
      if (err.response?.data?.detail) {
        errorMessage = typeof err.response.data.detail === 'string'
          ? err.response.data.detail
          : JSON.stringify(err.response.data.detail)
      } else if (err.message) {
        errorMessage = typeof err.message === 'string'
          ? err.message
          : JSON.stringify(err.message)
      } else if (err.response?.data) {
        // Handle Pydantic validation errors which might be objects
        const errorData = err.response.data
        if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail.map((e: any) =>
            typeof e === 'string' ? e : (e.msg || 'Validation error')
          ).join(', ')
        } else if (typeof errorData.detail === 'object') {
          errorMessage = 'Validation error: Please check your input'
        }
      }
      
      setError(errorMessage)
      toast.error(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  // Show invitation-only message if no token
  if (!token && isInvitationValid === false) {
    return (
      <PublicLayout
        title="Registration"
        description="Invitation-only registration"
      >
        <div className="w-full">
          <Card className="text-center">
            <CardHeader>
              <Lock className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <CardTitle className="text-xl">Registration is Invitation-Only</CardTitle>
              <CardDescription>
                AlphaHR registration is currently only available to users who have received an invitation.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-sm text-muted-foreground">
                <p>If you have received an invitation, please check your email for the registration link.</p>
                <p className="mt-2">If you believe this is an error, please contact your HR administrator.</p>
              </div>
              <Button asChild variant="outline" className="w-full">
                <Link href="/login">
                  Go to Login
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </PublicLayout>
    )
  }

  // Show loading while validating token
  if (isValidatingToken) {
    return (
      <PublicLayout
        title="Validating Invitation"
        description="Please wait while we validate your invitation"
      >
        <div className="w-full">
          <Card className="text-center">
            <CardContent className="pt-6">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Validating invitation...</p>
            </CardContent>
          </Card>
        </div>
      </PublicLayout>
    )
  }

  // Show invalid invitation message
  if (token && isInvitationValid === false) {
    return (
      <PublicLayout
        title="Invalid Invitation"
        description="This invitation is not valid"
      >
        <div className="w-full">
          <Card className="text-center">
            <CardHeader>
              <AlertCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
              <CardTitle className="text-xl text-red-600">Invalid Invitation</CardTitle>
              <CardDescription>
                This invitation is invalid, expired, or has already been used.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-sm text-muted-foreground">
                <p>Please contact your HR administrator to receive a new invitation.</p>
              </div>
              <Button asChild variant="outline" className="w-full">
                <Link href="/login">
                  Go to Login
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </PublicLayout>
    )
  }

  return (
    <PublicLayout
      title={token ? "Complete Registration" : "Register"}
      description={token ? "Complete your registration using the invitation link" : "Create a new account to access the HR System"}
    >
      <div className="w-full">
        {token && invitationData && (
          <Card className="mb-6 bg-blue-50 border-blue-200">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-3">
                <Mail className="h-5 w-5 text-blue-600" />
                <h3 className="font-medium text-blue-900">Invitation Details</h3>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Email:</span>
                  <span className="font-medium">{invitationData.email}</span>
                </div>
                {invitationData.role && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Role:</span>
                    <span className="font-medium">{invitationData.role.role_name}</span>
                  </div>
                )}
                {invitationData.department && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Department:</span>
                    <span className="font-medium">{invitationData.department.department_name}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Expires:</span>
                  <span className="font-medium">{new Date(invitationData.expires_at).toLocaleDateString()}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              name="username"
              type="text"
              placeholder="Choose a username"
              value={formData.username}
              onChange={handleChange}
              required
            />
            <p className="text-xs text-muted-foreground">
              This will be your login username (you can also login with your email)
            </p>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              name="email"
              type="email"
              placeholder="Enter your email"
              value={formData.email}
              onChange={handleChange}
              required
              disabled={!!(token && isInvitationValid)}
              className={token && isInvitationValid ? "bg-muted" : ""}
            />
            {token && isInvitationValid && (
              <p className="text-xs text-muted-foreground">Email is pre-filled from your invitation</p>
            )}
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="full_name">Full Name</Label>
            <Input
              id="full_name"
              name="full_name"
              type="text"
              placeholder="Enter your full name"
              value={formData.full_name}
              onChange={handleChange}
              required
              disabled={!!(token && isInvitationValid)}
              className={token && isInvitationValid ? "bg-muted" : ""}
            />
            {token && isInvitationValid && (
              <p className="text-xs text-muted-foreground">Full name is pre-filled from your invitation</p>
            )}
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              name="password"
              type="password"
              placeholder="Enter your password"
              value={formData.password}
              onChange={handleChange}
              required
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <Input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              placeholder="Confirm your password"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
            />
          </div>
          
          {error && (
            <div className="text-destructive text-sm text-center bg-destructive/10 p-3 rounded">{error}</div>
          )}
          
          <Button type="submit" className="w-full" disabled={isLoading || isValidatingToken}>
            {isLoading ? 'Creating Account...' : token ? 'Complete Registration' : 'Register'}
          </Button>
        </form>
        
        <div className="mt-4 text-center text-sm">
          <span className="text-gray-600">Already have an account?</span>{' '}
          <Link
            href="/login"
            className="text-blue-600 hover:underline"
            prefetch={false}
          >
            Login
          </Link>
        </div>
      </div>
    </PublicLayout>
  )
}