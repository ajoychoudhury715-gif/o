'use client';

export default function AssistantsPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Assistants</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card title="Manage Profiles" description="View and edit assistant profiles" />
        <Card title="My Workload" description="View personal workload" />
        <Card title="Availability" description="Set availability" />
        <Card title="Auto-Allocation" description="Automatic task allocation" />
        <Card title="Workload" description="Overall workload view" />
        <Card title="Attendance" description="Track attendance" />
      </div>
    </div>
  );
}

function Card({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow cursor-pointer">
      <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      <p className="text-gray-600 mt-2">{description}</p>
    </div>
  );
}
