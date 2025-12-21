
import Link from 'next/link'
import { Check } from 'lucide-react'

export default function PricingPage() {
  return (
    <div className="container mx-auto px-4 py-16">
      <div className="text-center mb-16">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Simple, Transparent Pricing</h1>
        <p className="text-xl text-gray-600">Choose the plan that fits your growth.</p>
      </div>

      <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
        {/* Starter */}
        <div className="bg-white p-8 rounded-2xl shadow-lg border border-gray-100">
          <div className="text-sm font-semibold text-blue-600 mb-2">STARTER</div>
          <div className="text-4xl font-bold mb-4">৳2,000<span className="text-lg text-gray-500">/mo</span></div>
          <ul className="space-y-3 mb-8">
            <li className="flex gap-2"><Check className="text-green-500 w-5 h-5"/> <span>Web Hosting (5GB)</span></li>
            <li className="flex gap-2"><Check className="text-green-500 w-5 h-5"/> <span>10 AI Videos/mo</span></li>
            <li className="flex gap-2"><Check className="text-green-500 w-5 h-5"/> <span>Free SSL</span></li>
          </ul>
          <Link href="/auth/signup?plan=starter" className="block w-full py-3 text-center bg-gray-100 rounded-lg hover:bg-gray-200 font-semibold text-gray-800">Start Trial</Link>
        </div>

        {/* Business */}
        <div className="bg-gradient-to-br from-purple-600 to-blue-600 text-white p-8 rounded-2xl shadow-xl transform md:scale-105">
          <div className="text-sm font-semibold mb-2 opacity-90">BUSINESS</div>
          <div className="text-4xl font-bold mb-4">৳3,500<span className="text-lg opacity-75">/mo</span></div>
          <ul className="space-y-3 mb-8">
            <li className="flex gap-2"><Check className="w-5 h-5"/> <span>VPS (2 CPU, 4GB RAM)</span></li>
            <li className="flex gap-2"><Check className="w-5 h-5"/> <span>20 AI Videos/mo</span></li>
            <li className="flex gap-2"><Check className="w-5 h-5"/> <span>Social Scheduler</span></li>
            <li className="flex gap-2"><Check className="w-5 h-5"/> <span>Priority Support</span></li>
          </ul>
          <Link href="/auth/signup?plan=business" className="block w-full py-3 text-center bg-white text-purple-600 rounded-lg hover:bg-gray-100 font-semibold">Start Trial</Link>
        </div>

        {/* Enterprise */}
        <div className="bg-white p-8 rounded-2xl shadow-lg border border-gray-100">
          <div className="text-sm font-semibold text-purple-600 mb-2">ENTERPRISE</div>
          <div className="text-4xl font-bold mb-4">৳6,000<span className="text-lg text-gray-500">/mo</span></div>
          <ul className="space-y-3 mb-8">
            <li className="flex gap-2"><Check className="text-green-500 w-5 h-5"/> <span>High Perf VPS (8GB)</span></li>
            <li className="flex gap-2"><Check className="text-green-500 w-5 h-5"/> <span>Unlimited Videos</span></li>
            <li className="flex gap-2"><Check className="text-green-500 w-5 h-5"/> <span>Custom Branding</span></li>
          </ul>
          <Link href="/auth/signup?plan=enterprise" className="block w-full py-3 text-center bg-gray-100 rounded-lg hover:bg-gray-200 font-semibold text-gray-800">Start Trial</Link>
        </div>
      </div>
    </div>
  )
}
