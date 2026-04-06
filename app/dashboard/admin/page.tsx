'use client';

export default function AdminPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Admin & Settings</h2>
      <p className="mb-6 max-w-3xl text-sm text-gray-600">
        Admin workflows are only represented as overview cards in the Next.js app right now while
        the deeper screens are being ported over.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="User Management" description="Manage system users" />
        <Card title="Storage & Backup" description="Data backup settings" />
        <Card title="Notifications" description="Configure notifications" />
        <Card title="Duties Manager" description="Manage duty assignments" />
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
