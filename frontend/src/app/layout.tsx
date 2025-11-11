import type { Metadata } from 'next'
import { Kumbh_Sans } from 'next/font/google'
import './globals.css'
import { AuthProvider } from '@/contexts/AuthContext'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { ThemeProvider } from '@/components/theme-provider'

const kumbhSans = Kumbh_Sans({
  subsets: ['latin'],
  variable: '--font-kumbh-sans',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'AlphaHR',
  description: 'Human Resource Management System',
  icons: {
    icon: '/favicon.png',
    apple: '/favicon.png',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={kumbhSans.className}>
        <div className="min-h-screen bg-background text-foreground" suppressHydrationWarning>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            <AuthProvider>
              <ErrorBoundary type="general">
                {children}
              </ErrorBoundary>
            </AuthProvider>
          </ThemeProvider>
        </div>
      </body>
    </html>
  )
}