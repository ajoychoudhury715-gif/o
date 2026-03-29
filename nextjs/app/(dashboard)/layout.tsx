import { Sidebar } from '@/components/Sidebar'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex h-screen bg-gradient-to-br from-medical-blue-50 to-blue-50">
      {/* Sidebar */}
      <div className="w-64 max-h-screen overflow-hidden">
        <Sidebar />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <div className="h-16 bg-white/40 glass-light px-8 flex items-center shadow-sm">
          <h2 className="text-xl font-semibold text-gray-800">Dental Bond Scheduler</h2>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto p-8">
          {children}
        </div>
      </div>
    </div>
  )
}
