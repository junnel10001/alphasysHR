'use client'

import React, { createContext, useContext, useState, useEffect } from 'react'
import { authService } from '@/lib/api'

interface User {
  id: number
  username: string
  email: string
  full_name: string
  role: string
  permissions: string[]
  phone?: string
  department?: string
  join_date?: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
    
    // Only run on client side
    const storedToken = localStorage.getItem('token')
    if (storedToken) {
      setToken(storedToken)
      // Try to get current user and permissions
      Promise.all([
        authService.getCurrentUser(),
        authService.getPermissions()
      ])
        .then(([userData, permissionsData]) => {
          // Combine user data with permissions
          const userWithPermissions = {
            ...userData,
            permissions: Array.isArray(permissionsData) ? permissionsData : permissionsData.permissions || []
          }
          setUser(userWithPermissions)
        })
        .catch((error) => {
          console.error('Error validating token:', error)
          // Token is invalid, remove it
          localStorage.removeItem('token')
          setToken(null)
          setUser(null)
        })
        .finally(() => {
          setIsLoading(false)
        })
    } else {
      setIsLoading(false)
    }
    //return () => {}
  }, [])

  const login = async (username: string, password: string) => {
    try {
      const response = await authService.login(username, password)
      const token = response.access_token
      
      // Store token first
      localStorage.setItem('token', token)
      setToken(token)
      
      // Get user info and permissions with error handling
      try {
        const [userData, permissionsData] = await Promise.all([
          authService.getCurrentUser(),
          authService.getPermissions()
        ])
        // Combine user data with permissions
        const userWithPermissions = {
          ...userData,
          permissions: Array.isArray(permissionsData) ? permissionsData : permissionsData.permissions || []
        }
        setUser(userWithPermissions)
        // Ensure user state is set before returning
        return userWithPermissions
      } catch (userError) {
        console.error('Failed to load user data:', userError)
        // If we can't get user info, clear everything and throw
        localStorage.removeItem('token')
        setToken(null)
        setUser(null)
        throw new Error('Failed to load user information. Please login again.')
      }
    } catch (error) {
      throw new Error('Invalid username or password')
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('token')
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}