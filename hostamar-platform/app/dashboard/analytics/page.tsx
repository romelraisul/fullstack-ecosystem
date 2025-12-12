'use client'

import { useState, useEffect } from 'react'
import { Activity, Users, DollarSign, Search, FileText } from 'lucide-react'

export default function AnalyticsDashboard() {
  const [metrics, setMetrics] = useState<any>(null)
  const [query, setQuery] = useState('')
  const [report, setReport] = useState('')
  const [loading, setLoading] = useState(false)
  const [researching, setResearching] = useState(false)

  useEffect(() => {
    fetch('/api/analytics')
      .then(res => res.json())
      .then(data => setMetrics(data))
      .catch(err => console.error(err))
  }, [])

  const handleResearch = async (e: React.FormEvent) => {
    e.preventDefault()
    setResearching(true)
    setReport('')
    
    try {
      const res = await fetch('/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      })
      const data = await res.json()
      if (data.report) {
        setReport(data.report)
      } else if (data.status === 'initiated') {
        setReport(`Research Initiated. Interaction ID: ${data.interactionId}\n(Polling not implemented in MVP UI yet)`)
      } else {
        setReport('No report generated.')
      }
    } catch (err) {
      console.error(err)
      setReport('Error executing research.')
    } finally {
      setResearching(false)
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Executive Analytics</h1>
        <p className="text-gray-500">Real-time platform insights and strategic intelligence.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <KpiCard 
          title="Total Users" 
          value={metrics?.totalUsers || '...'}
          icon={<Users className="h-6 w-6 text-blue-600" />}
          trend="+12% vs last month"
        />
        <KpiCard 
          title="Revenue (MRR)" 
          value={metrics?.monthlyRevenue ? `$${metrics.monthlyRevenue}` : '$0'}
          icon={<DollarSign className="h-6 w-6 text-green-600" />}
          trend="+5% vs last month"
        />
        <KpiCard 
          title="Active Subs" 
          value={metrics?.activeSubscriptions || '0'}
          icon={<Activity className="h-6 w-6 text-purple-600" />}
          trend="Stable"
        />
        <KpiCard 
          title="System Health" 
          value={metrics?.systemHealth || '...'}
          icon={<Activity className="h-6 w-6 text-red-600" />}
          trend="Optimal"
        />
      </div>

      {/* Deep Research Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-indigo-100 rounded-lg">
            <Search className="h-6 w-6 text-indigo-600" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Deep Market Research</h2>
            <p className="text-sm text-gray-500">Powered by Gemini Deep Research Agent</p>
          </div>
        </div>

        <form onSubmit={handleResearch} className="flex gap-4 mb-6">
          <input 
            type="text" 
            placeholder="e.g., Analyze VPS pricing trends in Southeast Asia..." 
            className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button 
            type="submit" 
            disabled={researching}
            className="px-6 py-3 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {researching ? 'Analyzing...' : 'Start Research'}
          </button>
        </form>

        {report && (
          <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
            <div className="flex items-center gap-2 mb-4 text-gray-700 font-semibold">
              <FileText className="h-5 w-5" />
              <h3>Research Report</h3>
            </div>
            <pre className="whitespace-pre-wrap font-sans text-gray-700 leading-relaxed">
              {report}
            </pre>
          </div>
        )}
      </div>

    </div>
  )
}

function KpiCard({ title, value, icon, trend }: any) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
      <div className="flex justify-between items-start mb-4">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <h3 className="text-2xl font-bold text-gray-900 mt-1">{value}</h3>
        </div>
        <div className="p-2 bg-gray-50 rounded-lg">
          {icon}
        </div>
      </div>
      <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full">
        {trend}
      </span>
    </div>
  )
}
