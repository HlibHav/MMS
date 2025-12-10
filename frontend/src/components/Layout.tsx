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
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <nav className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-semibold text-slate-50">Promo Scenario Co-Pilot</h1>
              <div className="hidden sm:flex sm:space-x-2">
                {navItems.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`inline-flex items-center rounded-lg px-3 py-2 text-sm font-medium transition ${
                      location.pathname === item.path
                        ? "bg-primary-500/10 text-primary-200"
                        : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"
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
