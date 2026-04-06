import type { UserRole, NavigationItem, Permission } from '@/types/rbac'
import type { User } from '@/types/auth'

// Default permissions for each role
const DEFAULT_ROLE_PERMISSIONS: Record<UserRole, string[]> = {
  admin: [
    // All pages and actions
    'page::Scheduling::Full Schedule',
    'page::Scheduling::Upcoming',
    'page::Scheduling::Ongoing',
    'page::Scheduling::Per OP Schedule',
    'page::Assistants::Workload',
    'page::Assistants::My Workload',
    'page::Assistants::Attendance',
    'page::Assistants::Availability',
    'page::Assistants::Manage Profiles',
    'page::Assistants::Auto Allocation',
    'page::Doctors::Workload',
    'page::Doctors::My Workload',
    'page::Doctors::Overview',
    'page::Doctors::Manage Profiles',
    'page::Doctors::Per Doctor Schedule',
    'page::Doctors::Summary',
    'page::Doctors::Week Off',
    'page::Admin::User Management',
    'page::Admin::Duties Manager',
    'page::Admin::Notifications',
    'page::Admin::Storage Backup',
    'action::schedule::add_appointment',
    'action::schedule::edit_appointment',
    'action::schedule::delete_appointment',
    'action::schedule::update_status',
    'action::schedule::auto_allocate',
    'action::schedule::manage_time_blocks',
    'action::operation::punch_in',
    'action::operation::punch_out',
    'action::operation::manage_duties',
    'action::operation::manage_reminders',
    'action::admin::save_controls',
    'action::admin::user_management',
    'action::admin::configure_permissions',
  ],

  frontdesk: [
    'page::Scheduling::Full Schedule',
    'page::Assistants::Workload',
    'page::Assistants::Attendance',
    'action::schedule::add_appointment',
    'action::schedule::edit_appointment',
    'action::schedule::delete_appointment',
    'action::schedule::update_status',
    'action::operation::punch_in',
    'action::operation::punch_out',
    'action::operation::manage_duties',
    'action::operation::manage_reminders',
  ],

  assistant: [
    'page::Scheduling::Full Schedule',
    'page::Assistants::My Workload',
    'page::Assistants::Availability',
    'page::Assistants::Manage Profiles',
    'action::operation::punch_in',
    'action::operation::punch_out',
    'action::operation::manage_duties',
    'action::operation::manage_reminders',
  ],

  doctor: [
    'page::Doctors::My Workload',
    'page::Doctors::Overview',
    'page::Doctors::Per Doctor Schedule',
    'page::Doctors::Summary',
    'page::Doctors::Week Off',
    'action::operation::manage_reminders',
  ],
}

// Navigation structure with role-based visibility
export const NAVIGATION_STRUCTURE: NavigationItem[] = [
  {
    id: 'scheduling',
    label: 'Scheduling',
    href: '/scheduling',
    icon: 'calendar',
    roles: ['admin', 'frontdesk', 'assistant'],
    children: [
      {
        id: 'full-schedule',
        label: 'Full Schedule',
        href: '/scheduling',
        roles: ['admin', 'frontdesk', 'assistant'],
        requiresPermission: 'page::Scheduling::Full Schedule',
      },
      {
        id: 'upcoming',
        label: 'Upcoming',
        href: '/scheduling/upcoming',
        roles: ['admin', 'frontdesk'],
        requiresPermission: 'page::Scheduling::Upcoming',
      },
      {
        id: 'ongoing',
        label: 'Ongoing',
        href: '/scheduling/ongoing',
        roles: ['admin', 'frontdesk'],
        requiresPermission: 'page::Scheduling::Ongoing',
      },
      {
        id: 'by-op',
        label: 'By Operation',
        href: '/scheduling/by-op',
        roles: ['admin', 'frontdesk'],
        requiresPermission: 'page::Scheduling::Per OP Schedule',
      },
    ],
  },
  {
    id: 'assistants',
    label: 'Assistants',
    href: '/assistants',
    icon: 'users',
    roles: ['admin', 'frontdesk', 'assistant'],
    children: [
      {
        id: 'workload',
        label: 'Team Workload',
        href: '/assistants/workload',
        roles: ['admin', 'frontdesk'],
        requiresPermission: 'page::Assistants::Workload',
      },
      {
        id: 'my-workload',
        label: 'My Workload',
        href: '/assistants/my-workload',
        roles: ['assistant'],
        requiresPermission: 'page::Assistants::My Workload',
      },
      {
        id: 'attendance',
        label: 'Attendance',
        href: '/assistants/attendance',
        roles: ['admin', 'frontdesk', 'assistant'],
        requiresPermission: 'page::Assistants::Attendance',
      },
      {
        id: 'availability',
        label: 'Availability',
        href: '/assistants/availability',
        roles: ['admin', 'assistant'],
        requiresPermission: 'page::Assistants::Availability',
      },
      {
        id: 'profiles',
        label: 'Manage Profiles',
        href: '/assistants/profiles',
        roles: ['admin'],
        requiresPermission: 'page::Assistants::Manage Profiles',
      },
    ],
  },
  {
    id: 'doctors',
    label: 'Doctors',
    href: '/doctors',
    icon: 'stethoscope',
    roles: ['admin', 'doctor'],
    children: [
      {
        id: 'doctor-workload',
        label: 'Team Workload',
        href: '/doctors/workload',
        roles: ['admin'],
        requiresPermission: 'page::Doctors::Workload',
      },
      {
        id: 'my-doctor-workload',
        label: 'My Workload',
        href: '/doctors/my-workload',
        roles: ['doctor'],
        requiresPermission: 'page::Doctors::My Workload',
      },
      {
        id: 'overview',
        label: 'Overview',
        href: '/doctors/overview',
        roles: ['admin', 'doctor'],
        requiresPermission: 'page::Doctors::Overview',
      },
      {
        id: 'doctor-profiles',
        label: 'Manage Profiles',
        href: '/doctors/profiles',
        roles: ['admin'],
        requiresPermission: 'page::Doctors::Manage Profiles',
      },
      {
        id: 'per-doctor',
        label: 'Per Doctor Schedule',
        href: '/doctors/schedule',
        roles: ['admin'],
        requiresPermission: 'page::Doctors::Per Doctor Schedule',
      },
      {
        id: 'week-off',
        label: 'Week Off',
        href: '/doctors/week-off',
        roles: ['admin', 'doctor'],
        requiresPermission: 'page::Doctors::Week Off',
      },
    ],
  },
  {
    id: 'admin',
    label: 'Admin',
    href: '/admin',
    icon: 'settings',
    roles: ['admin'],
    children: [
      {
        id: 'users',
        label: 'User Management',
        href: '/admin/users',
        roles: ['admin'],
        requiresPermission: 'page::Admin::User Management',
      },
      {
        id: 'duties',
        label: 'Duties',
        href: '/admin/duties',
        roles: ['admin'],
        requiresPermission: 'page::Admin::Duties Manager',
      },
      {
        id: 'notifications',
        label: 'Notifications',
        href: '/admin/notifications',
        roles: ['admin'],
        requiresPermission: 'page::Admin::Notifications',
      },
    ],
  },
]

/**
 * Get permissions for a user role
 */
export function getPermissionsForRole(role: UserRole): string[] {
  return DEFAULT_ROLE_PERMISSIONS[role] || []
}

/**
 * Check if user has a specific permission
 */
export function hasPermission(permissions: string[], permission: string): boolean {
  return permissions.includes(permission)
}

/**
 * Filter navigation items based on user role and permissions
 */
export function getFilteredNavigation(role: UserRole, permissions: string[]): NavigationItem[] {
  return NAVIGATION_STRUCTURE.filter((item) => {
    if (!item.roles.includes(role)) return false

    if (item.children) {
      item.children = item.children.filter((child) => {
        if (!child.roles.includes(role)) return false
        if (child.requiresPermission && !hasPermission(permissions, child.requiresPermission)) {
          return false
        }
        return true
      })

      return item.children.length > 0
    }

    if (item.requiresPermission && !hasPermission(permissions, item.requiresPermission)) {
      return false
    }

    return true
  })
}

/**
 * Check if user can access a page
 */
export function canAccessPage(role: UserRole, permissions: string[], pagePermission: string): boolean {
  return getPermissionsForRole(role).includes(pagePermission) && hasPermission(permissions, pagePermission)
}
