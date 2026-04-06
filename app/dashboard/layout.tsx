'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';

import { clearStoredSession, getStoredSession } from '../../lib/auth';
import type { UserRole } from '../../lib/types';

type NavItem = {
  href: string;
  label: string;
  icon: string;
  roles: UserRole[];
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const currentPath = pathname ?? '';
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [username, setUsername] = useState('User');
  const [role, setRole] = useState<UserRole | null>(null);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  useEffect(() => {
    const session = getStoredSession();
    if (!session) {
      router.replace('/auth/login');
      return;
    }

    setUsername(session.user.username);
    setRole(session.user.role);
  }, [router]);

  const navigation = useMemo<NavItem[]>(
    () => [
      {
        href: '/dashboard/scheduling',
        icon: '📅',
        label: 'Scheduling',
        roles: ['admin', 'frontdesk', 'assistant'],
      },
      {
        href: '/dashboard/assistants',
        icon: '👥',
        label: 'Assistants',
        roles: ['admin', 'frontdesk', 'assistant'],
      },
      {
        href: '/dashboard/doctors',
        icon: '🩺',
        label: 'Doctors',
        roles: ['admin', 'doctor'],
      },
      {
        href: '/dashboard/admin',
        icon: '⚙️',
        label: 'Admin',
        roles: ['admin'],
      },
    ],
    []
  );

  const visibleNavigation = role
    ? navigation.filter((item) => item.roles.includes(role))
    : navigation;

  const handleLogout = async () => {
    setIsLoggingOut(true);

    try {
      await fetch('/api/auth/logout', { method: 'POST' });
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      clearStoredSession();
      router.replace('/auth/login');
      router.refresh();
      setIsLoggingOut(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-100">
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-20'
        } flex flex-col border-r border-slate-200 bg-slate-950 text-white transition-all duration-300`}
      >
        <div className="p-4">
          <div className="mb-8 flex items-center gap-3">
            <div className="text-2xl">🦷</div>
            {sidebarOpen ? (
              <div>
                <p className="text-sm uppercase tracking-[0.2em] text-slate-400">Dashboard</p>
                <p className="font-semibold text-white">The Dental Bond</p>
              </div>
            ) : null}
          </div>
          <nav className="space-y-2">
            <NavItem
              active={pathname === '/dashboard'}
              href="/dashboard"
              icon="🏠"
              label="Overview"
              open={sidebarOpen}
            />
            {visibleNavigation.map((item) => (
              <NavItem
                key={item.href}
                active={currentPath.startsWith(item.href)}
                href={item.href}
                icon={item.icon}
                label={item.label}
                open={sidebarOpen}
              />
            ))}
          </nav>
        </div>

        <div className="mt-auto border-t border-slate-800 p-4">
          {sidebarOpen ? (
            <div className="mb-4">
              <p className="text-sm font-medium text-white">{username}</p>
              <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
                {role || 'loading'}
              </p>
            </div>
          ) : null}
          <button
            type="button"
            onClick={handleLogout}
            className="flex w-full items-center justify-center rounded-lg bg-slate-800 px-3 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isLoggingOut}
          >
            {isLoggingOut ? 'Signing out...' : sidebarOpen ? 'Sign Out' : '↩'}
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="border-b border-slate-200 bg-white/90 shadow-sm backdrop-blur">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              type="button"
              className="text-gray-500 transition hover:text-gray-700"
            >
              {sidebarOpen ? '✕' : '☰'}
            </button>
            <div className="text-right">
              <p className="text-sm font-medium text-gray-700">{username}</p>
              <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
                {role || 'loading'}
              </p>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-auto">
          <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 md:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

function NavItem({
  active,
  href,
  icon,
  label,
  open,
}: {
  active: boolean;
  href: string;
  icon: string;
  label: string;
  open: boolean;
}) {
  return (
    <Link
      href={href}
      className={`flex items-center space-x-3 rounded-lg px-4 py-2 transition-colors ${
        active ? 'bg-white text-slate-950' : 'hover:bg-slate-800'
      }`}
    >
      <span className="text-xl">{icon}</span>
      {open && <span>{label}</span>}
    </Link>
  );
}
