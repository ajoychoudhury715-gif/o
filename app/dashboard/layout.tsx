'use client';

import { useState } from 'react';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-20'
        } bg-gray-900 text-white transition-all duration-300`}
      >
        <div className="p-4">
          <div className="text-2xl font-bold mb-8">🦷</div>
          <nav className="space-y-2">
            <NavItem icon="📅" label="Scheduling" open={sidebarOpen} />
            <NavItem icon="👥" label="Assistants" open={sidebarOpen} />
            <NavItem icon="🩺" label="Doctors" open={sidebarOpen} />
            <NavItem icon="⚙️" label="Admin" open={sidebarOpen} />
          </nav>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="text-gray-500 hover:text-gray-700"
            >
              {sidebarOpen ? '✕' : '☰'}
            </button>
            <div className="text-right">
              <p className="text-sm font-medium text-gray-700">User Name</p>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8 py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

function NavItem({
  icon,
  label,
  open,
}: {
  icon: string;
  label: string;
  open: boolean;
}) {
  return (
    <a
      href="#"
      className="flex items-center space-x-3 px-4 py-2 rounded-lg hover:bg-gray-800 transition-colors"
    >
      <span className="text-xl">{icon}</span>
      {open && <span>{label}</span>}
    </a>
  );
}
