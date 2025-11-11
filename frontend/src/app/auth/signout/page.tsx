'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { LogOut, CheckCircle } from 'lucide-react'

export default function SignoutPage() {
  const router = useRouter()
  const { logout } = useAuth()

  useEffect(() => {
    // Perform logout when the page loads
    logout()
  }, [logout])

  const handleReturnToLogin = () => {
    router.push('/login')
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <CardTitle className="text-2xl font-semibold text-gray-900">
            Signed Out Successfully
          </CardTitle>
          <CardDescription>
            You have been successfully signed out of your account.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-center text-sm text-gray-600">
            <p>Thank you for using AlphaHR System.</p>
            <p className="mt-1">Your session has been securely terminated.</p>
          </div>
          <Button 
            onClick={handleReturnToLogin}
            className="w-full"
            size="lg"
          >
            <LogOut className="mr-2 h-4 w-4" />
            Return to Login
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}