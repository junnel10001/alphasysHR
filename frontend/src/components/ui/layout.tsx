'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { AlphaSysLogo } from './logo'
import { ThemeToggle } from './theme-toggle'
import { Breadcrumb, useBreadcrumbs } from './breadcrumb'
import Image from 'next/image'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import {
  Home,
  Users,
  Clock,
  FileText,
  Activity,
  Download,
  LogOut,
  Menu,
  X,
  Settings,
  User,
  HelpCircle,
  Mail,
} from 'lucide-react'

interface LayoutProps {
  children: React.ReactNode
}

const navigation = [
  {
    title: 'Main',
    items: [
      { name: 'Home', href: '/', icon: Home },
    ],
  },
  {
    title: 'HR Management',
    items: [
      { name: 'Employees', href: '/employees', icon: Users },
      { name: 'Attendance', href: '/attendance', icon: Clock },
      { name: 'Leave', href: '/leave', icon: FileText },
    ],
  },
  {
    title: 'Finance',
    items: [
      { name: 'Payroll', href: '/payroll', icon: Activity },
      { name: 'Overtime', href: '/overtime', icon: Clock },
    ],
  },
  {
    title: 'Reports',
    items: [
      { name: 'Export', href: '/export', icon: Download },
    ],
  },
]

export function Layout({ children }: LayoutProps) {
  const pathname = typeof window !== 'undefined' ? usePathname() : ''
  const [sidebarOpen, setSidebarOpen] = React.useState(false)

  const NavItems = navigation.map((section) => (
    <div key={section.title} className="mb-6">
      <div className="px-3 py-2">
        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          {section.title}
        </h3>
      </div>
      <div className="space-y-1">
        {section.items.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              prefetch={false}
              className={cn(
                'flex items-center px-3 py-2 text-sm font-medium rounded-md transition-all duration-200 touch-manipulation',
                isActive
                  ? 'bg-alphasys text-white shadow-sm'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground hover:shadow-sm'
              )}
            >
              <item.icon className="mr-3 h-4 w-4" />
              {item.name}
            </Link>
          )
        })}
      </div>
    </div>
  ))

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile sidebar */}
      <div
        className={cn(
          'fixed inset-0 z-50 lg:hidden',
          sidebarOpen ? 'block' : 'hidden'
        )}
      >
        {/* Backdrop overlay with fade animation */}
        <div
          className={cn(
            'fixed inset-0 bg-black/60 transition-all duration-300 ease-in-out',
            sidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
          )}
          onClick={() => setSidebarOpen(false)}
        />
        
        {/* Sidebar with slide animation */}
        <div
          className={cn(
            'fixed inset-y-0 left-0 w-64 bg-background border-r shadow-xl transform transition-transform duration-300 ease-in-out',
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          )}
        >
          <div className="flex h-16 items-center justify-between px-4 border-b">
              <AlphaSysLogo size="md" />
            <div className="flex items-center gap-x-2">
              <ThemeToggle />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSidebarOpen(false)}
                className="hover:bg-accent rounded-md p-2 touch-manipulation"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
          <nav className="p-4 overflow-y-auto space-y-1">
            {NavItems}
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex min-h-0 flex-1 flex-col border-r bg-background">
          <div className="flex h-16 items-center px-4 border-b">
              <AlphaSysLogo size="md" />
            <div className="ml-auto">
              <ThemeToggle />
            </div>
          </div>
          <nav className="flex-1 overflow-y-auto p-4 space-y-1">
            {NavItems}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top navigation */}
        <header className="sticky top-0 z-40 flex h-16 items-center gap-x-4 border-b bg-background px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
          <Button
            variant="ghost"
            size="sm"
            className="lg:hidden hover:bg-accent rounded-md p-2 touch-manipulation"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </Button>
          
          <div className="flex flex-1 items-center justify-between">
            <div className="flex items-center gap-x-4">
              <div className="flex items-center gap-x-2 flex-1 min-w-0">
                <Breadcrumb items={useBreadcrumbs().breadcrumbs} className="flex-1 min-w-0" />
                {/*
                  <h2 className="text-lg font-semibold capitalize truncate ml-2">
                  {pathname.split('/').pop() || 'Dashboard'}
                </h2>
                */}
              </div>
            </div>
             
            <div className="flex items-center gap-x-4">
              <ThemeToggle />
              
              {/* User Profile Dropdown */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="relative h-8 w-8 rounded-full hover:bg-accent/50 transition-all duration-200"
                    aria-label="User profile menu"
                    aria-expanded="false"
                    aria-haspopup="menu"
                  >
                    <Avatar className="h-8 w-8">
                      <AvatarImage src="/avatars/01.png" alt="User avatar" />
                      <AvatarFallback>JD</AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end" forceMount>
                  <DropdownMenuLabel className="py-2">
                    <div className="flex flex-col space-y-1">
                      <span className="text-sm font-medium leading-none">John Doe</span>
                      <span className="text-xs leading-none text-muted-foreground">john.doe@alphasys.com</span>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild className="cursor-pointer hover:bg-accent/50 transition-colors duration-150" role="menuitem">
                    <Link href="/profile" className="flex items-center" role="menuitem">
                      <User className="mr-2 h-4 w-4" />
                      <span>Profile</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild className="cursor-pointer hover:bg-accent/50 transition-colors duration-150" role="menuitem">
                    <Link href="/settings" className="flex items-center" role="menuitem">
                      <Settings className="mr-2 h-4 w-4" />
                      <span>Settings</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild className="cursor-pointer hover:bg-accent/50 transition-colors duration-150" role="menuitem">
                    <Link href="/help" className="flex items-center" role="menuitem">
                      <HelpCircle className="mr-2 h-4 w-4" />
                      <span>Help & Support</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild className="cursor-pointer hover:bg-accent/50 transition-colors duration-150 text-red-600 focus:text-red-600 focus:bg-red-50/50" role="menuitem">
                    <Link href="/auth/signout" className="flex items-center" role="menuitem">
                      <LogOut className="mr-2 h-4 w-4" />
                      <span>Sign out</span>
                    </Link>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="py-6">
          <div className="px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}