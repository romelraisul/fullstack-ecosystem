
'use client'

import { useState } from 'react'
import { CheckCircle, Circle, Video, Server } from 'lucide-react'

export default function Dashboard() {
  const [tasks, setTasks] = useState([
    { id: 1, title: 'Create Account', completed: true },
    { id: 2, title: 'Complete Business Profile', completed: false },
    { id: 3, title: 'Generate First Video', completed: false },
    { id: 4, title: 'Upgrade to Pro', completed: false },
  ])

  const progress = Math.round((tasks.filter(t => t.completed).length / tasks.length) * 100)

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Welcome Header */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500">Welcome back! Here's what's happening today.</p>
        </div>
        <div className="text-right">
          <p className="text-sm font-medium text-gray-500">Onboarding Progress</p>
          <div className="flex items-center gap-3">
            <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div className="h-full bg-green-500 transition-all duration-500" style={{ width: `${progress}%` }}></div>
            </div>
            <span className="text-lg font-bold text-green-600">{progress}%</span>
          </div>
        </div>
      </div>

      {/* Onboarding Checklist */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <h2 className="text-lg font-semibold mb-4">🚀 Getting Started</h2>
        <div className="space-y-3">
          {tasks.map(task => (
            <div key={task.id} className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-lg transition">
              {task.completed ? 
                <CheckCircle className="w-5 h-5 text-green-500" /> : 
                <Circle className="w-5 h-5 text-gray-300" />
              }
              <span className={task.completed ? 'text-gray-500 line-through' : 'text-gray-900'}>{task.title}</span>
              {!task.completed && task.id === 3 && (
                <button className="ml-auto px-3 py-1 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700">
                  Create Now
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gradient-to-br from-purple-50 to-white p-6 rounded-xl border border-purple-100 shadow-sm hover:shadow-md transition cursor-pointer">
          <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
            <Video className="w-6 h-6 text-purple-600" />
          </div>
          <h3 className="text-xl font-bold mb-2">Video Generator</h3>
          <p className="text-gray-600 mb-4">Create AI-powered marketing videos for your business.</p>
          <span className="text-purple-600 font-medium">Open Generator →</span>
        </div>

        <div className="bg-gradient-to-br from-blue-50 to-white p-6 rounded-xl border border-blue-100 shadow-sm hover:shadow-md transition cursor-pointer">
          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
            <Server className="w-6 h-6 text-blue-600" />
          </div>
          <h3 className="text-xl font-bold mb-2">Cloud Hosting</h3>
          <p className="text-gray-600 mb-4">Manage your VPS, domains, and web hosting services.</p>
          <span className="text-blue-600 font-medium">Manage Server →</span>
        </div>
      </div>
    </div>
  )
}
