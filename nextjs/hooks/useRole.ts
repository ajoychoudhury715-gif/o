'use client'

import { useMemo } from 'react'
import type { UserRole, NavigationItem } from '@/types/rbac'
import { getPermissionsForRole, getFilteredNavigation, hasPermission, canAccessPage } from '@/lib/rbac'
import { useAuth } from './useAuth'

interface UseRoleReturn {
  role: UserRole | null
  permissions: string[]
  canAccess: (permission: string) => boolean
  canAccessPage: (pagePermission: string) => boolean
  filteredNavigation: NavigationItem[]
}

export function useRole(): UseRoleReturn {
  const { user } = useAuth()
  const role = user?.role as UserRole | null

  const permissions = useMemo(() => {
    if (!role) return []
    return getPermissionsForRole(role)
  }, [role])

  const filteredNavigation = useMemo(() => {
    if (!role) return []
    return getFilteredNavigation(role, permissions)
  }, [role, permissions])

  const canAccess = (permission: string): boolean => {
    return hasPermission(permissions, permission)
  }

  const accessPage = (pagePermission: string): boolean => {
    if (!role) return false
    return canAccessPage(role, permissions, pagePermission)
  }

  return {
    role,
    permissions,
    canAccess,
    canAccessPage: accessPage,
    filteredNavigation,
  }
}
