'use client';

export default function DoctorsPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Doctors</h2>
      <p className="mb-6 max-w-3xl text-sm text-gray-600">
        The doctor-specific screens are outlined here, but their detailed route migration is still
        in progress.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card title="Manage Profiles" description="View and edit doctor profiles" />
        <Card title="My Workload" description="View personal workload" />
        <Card title="Overview" description="General overview" />
        <Card title="Summary" description="Workload summary" />
        <Card title="Per-Doctor Schedule" description="Individual schedules" />
        <Card title="Week Off" description="Manage time off" />
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
    <div className="rounded-lg bg-white p-6 shadow">
      <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      <p className="text-gray-600 mt-2">{description}</p>
    </div>
  );
}
