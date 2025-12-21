import Link from 'next/link'
import { Button } from '@/components/ui/Button'
import { Home, Search, HelpCircle, HardDrive, FileQuestion } from 'lucide-react'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: '404 - Page Not Found | Hostamar',
  description: 'The page you are looking for does not exist.',
  robots: {
    index: false,
    follow: true,
  },
}

export default function NotFound() {
  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center bg-gray-50 px-4 py-16">
      {/* Visual Error Indicator */}
      <div className="relative mb-8">
        <h1 className="text-9xl font-extrabold text-gray-200 tracking-tighter">404</h1>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="bg-blue-100 p-4 rounded-full">
            <FileQuestion className="w-12 h-12 text-blue-600" />
          </span>
        </div>
      </div>

      {/* Text Content */}
      <div className="text-center max-w-2xl mx-auto space-y-4 mb-12">
        <h2 className="text-3xl font-bold text-gray-900">
          Oops! This page has drifted into the cloud.
        </h2>
        <p className="text-lg text-gray-600">
          We couldn't find the page you were looking for. It might have been removed, 
          renamed, or didn't exist in the first place.
        </p>
      </div>

      {/* Primary Action */}
      <div className="mb-16">
        <Link href="/">
          <Button size="lg" className="flex items-center gap-2">
            <Home className="w-4 h-4" />
            Back to Homepage
          </Button>
        </Link>
      </div>

      {/* Helpful Links Grid (SEO/UX) */}
      <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link 
          href="/pricing" 
          className="group p-6 bg-white rounded-xl shadow-sm border border-gray-100 hover:shadow-md hover:border-blue-200 transition-all duration-200"
        >
          <div className="bg-blue-50 w-10 h-10 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
            <HardDrive className="w-5 h-5 text-blue-600" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-1 group-hover:text-blue-600">View Pricing</h3>
          <p className="text-sm text-gray-500">Explore our cloud hosting and AI video plans.</p>
        </Link>

        <Link 
          href="/dashboard" 
          className="group p-6 bg-white rounded-xl shadow-sm border border-gray-100 hover:shadow-md hover:border-blue-200 transition-all duration-200"
        >
          <div className="bg-purple-50 w-10 h-10 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
            <Search className="w-5 h-5 text-purple-600" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-1 group-hover:text-purple-600">Dashboard</h3>
          <p className="text-sm text-gray-500">Manage your hosting and generated videos.</p>
        </Link>

        <Link 
          href="/contact" 
          className="group p-6 bg-white rounded-xl shadow-sm border border-gray-100 hover:shadow-md hover:border-blue-200 transition-all duration-200"
        >
          <div className="bg-green-50 w-10 h-10 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
            <HelpCircle className="w-5 h-5 text-green-600" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-1 group-hover:text-green-600">Help Center</h3>
          <p className="text-sm text-gray-500">Contact our support team for assistance.</p>
        </Link>
      </div>
    </div>
  )
}