import type { Metadata } from 'next'
import '../styles/globals.css'

export const metadata: Metadata = {
  title: 'The Dental Bond - Clinic Scheduler',
  description: 'Advanced scheduling system for dental clinics with role-based access control',
  viewport: 'width=device-width, initial-scale=1',
  icons: { icon: '🦷' },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="description" content="The Dental Bond - Professional clinic scheduling" />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}

