import React from 'react'
import Link from 'next/link'
import Image from 'next/image'

interface LogoProps {
  className?: string
  size?: 'sm' | 'md' | 'lg'
}

export function AlphaSysLogo({ className = '', size = 'md' }: LogoProps) {
  const sizeClasses = {
    sm: 'h-6 w-auto',
    md: 'h-8 w-auto',
    lg: 'h-10 w-auto'
  }

  return (
    <Link href="/" className={`flex items-center space-x-2 ${className}`} prefetch={false}>
      <div className="flex items-center">
        <Image
          src="/logo.png"
          alt="AlphaSys Logo"
          width={size === 'sm' ? 24 : size === 'md' ? 32 : 40}
          height={size === 'sm' ? 24 : size === 'md' ? 32 : 40}
          className={sizeClasses[size]}
          priority
          unoptimized
        />
      </div>
    </Link>
  )
}