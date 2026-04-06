// RBAC types
export type UserRole = 'admin' | 'frontdesk' | 'assistant' | 'doctor'

export interface Permission {
  functionId: string
  name: string
  category: string
}

export interface RolePermissions {
  role: UserRole
  permissions: Permission[]
  createdAt: string
}

export interface UserPermissionOverride {
  userId: string
  permissions: Permission[]
  createdAt: string
}

export interface NavigationItem {
  id: string
  label: string
  href: string
  icon?: string
  children?: NavigationItem[]
  roles: UserRole[]
  requiresPermission?: string
}
