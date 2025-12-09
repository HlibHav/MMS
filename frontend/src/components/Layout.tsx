import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ChatWidget } from './ChatWidget'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  
  const navItems = [
    { path: '/discovery', label: 'Discovery' },
    { path: '/scenarios', label: 'Scenario Lab' },
    { path: '/optimization', label: 'Optimization' },
    { path: '/creative', label: 'Creative' },
  ]
  
  return (
    <div className="min-h-screen bg-surface-50 text-slate-900">
      <nav className="border-b border-border bg-white shadow-card">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-semibold">Promo Scenario Co-Pilot</h1>
              <div className="hidden sm:flex sm:space-x-6">
                {navItems.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`inline-flex items-center rounded-md px-3 py-2 text-sm font-medium transition ${
                      location.pathname === item.path
                        ? "bg-primary-50 text-primary-700"
                        : "text-muted hover:bg-surface-100 hover:text-slate-900"
                    }`}
                  >
                    {item.label}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      </nav>
      <main className="mx-auto max-w-7xl py-6 sm:px-6 lg:px-8">{children}</main>
      <ChatWidget />
    </div>
  )
}
