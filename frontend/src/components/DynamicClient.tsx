'use client'

import { useState, useEffect } from 'react'

interface DynamicClientProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

export function DynamicClient({ children, fallback = null }: DynamicClientProps) {
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  if (!isClient) {
    return <>{fallback}</>
  }

  return <>{children}</>
}