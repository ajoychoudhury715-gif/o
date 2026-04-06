'use client';

export default function SchedulingPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Scheduling</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card title="Full Schedule" description="View complete schedule" />
        <Card title="Schedule by OP" description="View by operating room" />
        <Card title="Ongoing" description="Current appointments" />
        <Card title="Upcoming" description="Future appointments" />
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
