'use client'

import React from 'react'
import { Layout } from '@/components/ui/layout'
import { ProtectedRoute } from '@/components/ProtectedRoute'

interface LayoutWrapperProps {
  children: React.ReactNode
  requiredRole?: string
}

export function LayoutWrapper({ children, requiredRole }: LayoutWrapperProps) {
  return (
    <ProtectedRoute requiredRole={requiredRole}>
      <Layout>{children}</Layout>
    </ProtectedRoute>
  )
}