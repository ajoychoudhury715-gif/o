/**
 * Convert time string (HH:MM) to minutes since midnight
 */
export function timeToMinutes(time: string): number {
  const [hours, minutes] = time.split(':').map(Number)
  return hours * 60 + minutes
}

/**
 * Convert minutes since midnight to HH:MM format
 */
export function minutesToTime(minutes: number): string {
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`
}

/**
 * Get current time in IST (UTC+5:30)
 */
export function getCurrentTimeIST(): Date {
  const now = new Date()
  const istOffset = 5.5 * 60 * 60 * 1000 // IST is UTC+5:30
  const utcTime = now.getTime() + now.getTimezoneOffset() * 60 * 1000
  return new Date(utcTime + istOffset)
}

/**
 * Format date as YYYY-MM-DD
 */
export function formatDateISO(date: Date): string {
  return date.toISOString().split('T')[0]
}

/**
 * Check if appointment is currently ongoing
 */
export function isAppointmentOngoing(inTime: string, outTime: string): boolean {
  const now = new Date()
  const currentMinutes = now.getHours() * 60 + now.getMinutes()
  const inMinutes = timeToMinutes(inTime)
  const outMinutes = timeToMinutes(outTime)

  return currentMinutes >= inMinutes && currentMinutes <= outMinutes
}

/**
 * Check if appointment is in the next N minutes
 */
export function isAppointmentUpcoming(inTime: string, minutes: number = 15): boolean {
  const now = new Date()
  const currentMinutes = now.getHours() * 60 + now.getMinutes()
  const inMinutes = timeToMinutes(inTime)
  const minuteDifference = inMinutes - currentMinutes

  return minuteDifference > 0 && minuteDifference <= minutes
}

/**
 * Get week day number (0-6, where 0 is Sunday)
 */
export function getWeekDay(date: Date): number {
  return date.getDay()
}

/**
 * Format time display
 */
export function formatTime(time: string): string {
  const [hours, minutes] = time.split(':')
  const hour = parseInt(hours, 10)
  const period = hour >= 12 ? 'PM' : 'AM'
  const displayHour = hour % 12 || 12
  return `${displayHour}:${minutes} ${period}`
}

/**
 * Get duration in minutes between two times
 */
export function getDuration(inTime: string, outTime: string): number {
  const inMinutes = timeToMinutes(inTime)
  const outMinutes = timeToMinutes(outTime)
  return Math.max(outMinutes - inMinutes, 0)
}

/**
 * Format duration in hours and minutes
 */
export function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (hours === 0) {
    return `${mins}m`
  }
  if (mins === 0) {
    return `${hours}h`
  }
  return `${hours}h ${mins}m`
}
