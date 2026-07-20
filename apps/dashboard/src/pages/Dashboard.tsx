import { Activity, Bot, BarChart3, CheckCircle, AlertCircle } from 'lucide-react'

export default function Dashboard() {
  return (
    <div className="p-6">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">AiFinPay AOS Dashboard</h1>
        <p className="text-gray-600 mt-2">Autonomous Growth OS - AI-powered marketing automation</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Active Campaigns"
          value="3"
          icon={<Activity className="w-5 h-5" />}
          trend="+2 this week"
        />
        <StatCard
          title="Agents Running"
          value="8"
          icon={<Bot className="w-5 h-5" />}
          trend="All operational"
        />
        <StatCard
          title="Content Published"
          value="24"
          icon={<CheckCircle className="w-5 h-5" />}
          trend="+12 this week"
        />
        <StatCard
          title="Pending Approvals"
          value="5"
          icon={<AlertCircle className="w-5 h-5" />}
          trend="Needs review"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Recent Activity
          </h2>
          <div className="space-y-4">
            <ActivityItem
              title="Market Intelligence Agent completed analysis"
              time="2 minutes ago"
              status="success"
            />
            <ActivityItem
              title="Content Strategy Agent created draft"
              time="15 minutes ago"
              status="pending"
            />
            <ActivityItem
              title="Social Publishing Agent published to X"
              time="1 hour ago"
              status="success"
            />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <button className="w-full bg-primary-600 text-white py-2 px-4 rounded hover:bg-primary-700 transition">
              Create New Campaign
            </button>
            <button className="w-full bg-gray-200 text-gray-800 py-2 px-4 rounded hover:bg-gray-300 transition">
              View Content Queue
            </button>
            <button className="w-full bg-gray-200 text-gray-800 py-2 px-4 rounded hover:bg-gray-300 transition">
              Review Analytics
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ title, value, icon, trend }: { title: string; value: string; icon: React.ReactNode; trend: string }) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="text-gray-600">{title}</div>
        <div className="text-primary-600">{icon}</div>
      </div>
      <div className="text-3xl font-bold text-gray-900">{value}</div>
      <div className="text-sm text-gray-500 mt-2">{trend}</div>
    </div>
  )
}

function ActivityItem({ title, time, status }: { title: string; time: string; status: 'success' | 'pending' }) {
  const statusColors = {
    success: 'bg-green-100 text-green-800',
    pending: 'bg-yellow-100 text-yellow-800',
  }

  return (
    <div className="flex items-start justify-between p-3 bg-gray-50 rounded">
      <div>
        <div className="font-medium text-gray-900">{title}</div>
        <div className="text-sm text-gray-500">{time}</div>
      </div>
      <span className={`px-2 py-1 rounded text-xs font-medium ${statusColors[status]}`}>
        {status}
      </span>
    </div>
  )
}
