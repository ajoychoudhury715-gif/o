'use client'

import { useRole } from '@/hooks/useRole'
import { useAuth } from '@/hooks/useAuth'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Calendar,
  Users,
  Stethoscope,
  Settings,
  LogOut,
  ChevronDown,
  User,
} from 'lucide-react'
import { useState } from 'react'

const iconMap: Record<string, React.ReactNode> = {
  calendar: <Calendar size={20} />,
  users: <Users size={20} />,
  stethoscope: <Stethoscope size={20} />,
  settings: <Settings size={20} />,
}

export function Sidebar() {
  const { filteredNavigation, role } = useRole()
  const { user, logout } = useAuth()
  const pathname = usePathname()
  const [expandedItems, setExpandedItems] = useState<string[]>([])

  const toggleExpanded = (itemId: string) => {
    setExpandedItems((prev) =>
      prev.includes(itemId) ? prev.filter((id) => id !== itemId) : [...prev, itemId]
    )
  }

  const isActive = (href: string) => pathname === href

  return (
    <div className="sidebar">
      {/* Logo/Header */}
      <div className="pb-4 border-b border-white/20">
        <h1 className="text-2xl font-bold text-gradient">🦷 Dental Bond</h1>
        <p className="text-xs text-gray-600 mt-1">Clinic Scheduler</p>
      </div>

      {/* User Info */}
      <div className="glass p-3 rounded-lg">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-medical-blue-600 flex items-center justify-center text-white">
            <User size={20} />
          </div>
          <div className="flex-1">
            <p className="font-medium text-sm">{user?.username}</p>
            <p className="text-xs text-gray-600 capitalize">{role}</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-2">
        {filteredNavigation.map((item) => (
          <div key={item.id}>
            <div className="flex items-center">
              {item.children ? (
                <button
                  onClick={() => toggleExpanded(item.id)}
                  className="flex-1 flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/20 transition-colors text-gray-700"
                >
                  {iconMap[item.icon || 'calendar']}
                  <span className="flex-1 text-left font-medium">{item.label}</span>
                  <ChevronDown
                    size={16}
                    className={`transition-transform ${expandedItems.includes(item.id) ? 'rotate-180' : ''}`}
                  />
                </button>
              ) : (
                <Link
                  href={item.href}
                  className={`flex-1 flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                    isActive(item.href)
                      ? 'bg-medical-blue-500 text-white'
                      : 'text-gray-700 hover:bg-white/20'
                  }`}
                >
                  {iconMap[item.icon || 'calendar']}
                  <span className="font-medium">{item.label}</span>
                </Link>
              )}
            </div>

            {/* Sub-items */}
            {item.children && expandedItems.includes(item.id) && (
              <div className="ml-4 space-y-1">
                {item.children.map((child) => (
                  <Link
                    key={child.id}
                    href={child.href}
                    className={`block px-3 py-2 rounded-lg transition-colors text-sm ${
                      isActive(child.href)
                        ? 'bg-medical-blue-500 text-white'
                        : 'text-gray-700 hover:bg-white/20'
                    }`}
                  >
                    {child.label}
                  </Link>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>

      {/* Logout Button */}
      <button
        onClick={() => logout()}
        className="w-full mt-4 flex items-center gap-3 px-3 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors font-medium"
      >
        <LogOut size={20} />
        Logout
      </button>
    </div>
  )
}
