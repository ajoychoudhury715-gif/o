export default function Home() {
  return (
    <div className="space-y-8">
      <div className="card">
        <h1 className="text-3xl font-bold text-gradient mb-4">Welcome to The Dental Bond</h1>
        <p className="text-gray-700 mb-6">
          Professional clinic scheduling system with advanced role-based access control and integration capabilities.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="glass p-6 rounded-xl">
            <div className="text-4xl mb-3">📅</div>
            <h3 className="font-semibold text-lg mb-2">Smart Scheduling</h3>
            <p className="text-sm text-gray-600">Intelligent appointment allocation with configurable rules</p>
          </div>
          <div className="glass p-6 rounded-xl">
            <div className="text-4xl mb-3">👥</div>
            <h3 className="font-semibold text-lg mb-2">Team Management</h3>
            <p className="text-sm text-gray-600">Manage doctors, assistants, and staff workload efficiently</p>
          </div>
          <div className="glass p-6 rounded-xl">
            <div className="text-4xl mb-3">🔐</div>
            <h3 className="font-semibold text-lg mb-2">Role-Based Access</h3>
            <p className="text-sm text-gray-600">Fine-grained permissions for admin, frontdesk, and staff</p>
          </div>
        </div>
      </div>
    </div>
  )
}
