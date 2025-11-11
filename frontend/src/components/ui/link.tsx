'use client'

import React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

interface CustomLinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  href: string
  children: React.ReactNode
  prefetch?: boolean
}

export const CustomLink = React.forwardRef<HTMLAnchorElement, CustomLinkProps>(
  ({ href, children, prefetch = false, ...props }, ref) => {
    const router = useRouter()
    
    // Handle client-side navigation to prevent hydration issues
    const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
      e.preventDefault()
      router.push(href)
    }

    return (
      <Link
        href={href}
        prefetch={prefetch}
        onClick={prefetch === false ? handleClick : undefined}
        ref={ref}
        {...props}
      >
        {children}
      </Link>
    )
  }
)

CustomLink.displayName = 'CustomLink'