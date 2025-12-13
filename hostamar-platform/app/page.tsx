import { Metadata } from 'next';
import Link from 'next/link';
import { Video, Cloud, Zap, Shield, Users, TrendingUp } from 'lucide-react';

export const metadata: Metadata = {
  title: 'Hostamar - Cloud Hosting + AI Marketing Videos',
  description: 'Get cloud hosting and professional marketing videos for your business',
};

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="container mx-auto px-4 py-6">
        <nav className="flex justify-between items-center">
          <div className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Hostamar.com
          </div>
          <div className="flex gap-4">
            <Link href="/login" className="px-4 py-2 text-gray-700 hover:text-blue-600">
              Login
            </Link>
            <Link 
              href="/signup" 
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Start Free Trial
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
            AI-Powered Cloud Hosting & Automated Marketing
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            হোস্টিং সার্ভিস + AI-powered মার্কেটিং ভিডিও। আপনার ব্যবসার জন্য প্রতি সপ্তাহে 10+ professional videos তৈরি হবে!
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link 
              href="/signup" 
              className="px-8 py-4 bg-blue-600 text-white text-lg rounded-lg hover:bg-blue-700 transition shadow-lg"
            >
              7 Days Free Trial →
            </Link>
            <Link 
              href="#pricing" 
              className="px-8 py-4 bg-white text-blue-600 text-lg rounded-lg hover:bg-gray-50 transition border-2 border-blue-600"
            >
              See Pricing
            </Link>
          </div>
          
          {/* Trust Badges */}
          <div className="mt-12 flex justify-center gap-8 text-sm text-gray-500">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-green-500" />
              <span>99.9% Uptime</span>
            </div>
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5 text-blue-500" />
              <span>100+ Happy Customers</span>
            </div>
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-yellow-500" />
              <span>Setup in 24 Hours</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-20">
        <h2 className="text-4xl font-bold text-center mb-12">কেন Hostamar?</h2>
        <div className="grid md:grid-cols-3 gap-8">
          {/* Feature 1 */}
          <div className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <Cloud className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="text-2xl font-bold mb-3">Cloud Hosting</h3>
            <p className="text-gray-600 mb-4">
              VPS, RDP, Web Hosting, Storage - সব এক জায়গায়। দ্রুত, secure, এবং reliable।
            </p>
            <ul className="text-sm text-gray-500 space-y-2">
              <li>✓ 99.9% uptime guarantee</li>
              <li>✓ SSD storage</li>
              <li>✓ 24/7 monitoring</li>
              <li>✓ Free SSL certificate</li>
            </ul>
          </div>

          {/* Feature 2 */}
          <div className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition border-2 border-purple-200">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <Video className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="text-2xl font-bold mb-3">AI Marketing Videos</h3>
            <p className="text-gray-600 mb-4">
              প্রতি সপ্তাহে 10+ professional videos। শুধু আপনার business info দিন, বাকি সব automatic!
            </p>
            <ul className="text-sm text-gray-500 space-y-2">
              <li>✓ AI-generated scripts</li>
              <li>✓ Professional voice-over</li>
              <li>✓ Custom branding</li>
              <li>✓ Ready to post</li>
            </ul>
            <div className="mt-4 px-3 py-1 bg-purple-100 text-purple-700 text-xs font-semibold rounded-full inline-block">
              🔥 Most Popular
            </div>
          </div>

          {/* Feature 3 */}
          <div className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="text-2xl font-bold mb-3">Free Marketing</h3>
            <p className="text-gray-600 mb-4">
              আপনার customers রা videos শেয়ার করবে → আপনার brand promote হবে → নতুন customers আসবে!
            </p>
            <ul className="text-sm text-gray-500 space-y-2">
              <li>✓ Social media ready</li>
              <li>✓ Your branding included</li>
              <li>✓ Viral content strategy</li>
              <li>✓ Analytics dashboard</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="container mx-auto px-4 py-20 bg-gray-50 rounded-3xl">
        <h2 className="text-4xl font-bold text-center mb-4">Simple Pricing</h2>
        <p className="text-center text-gray-600 mb-12">7 days free trial. No credit card required.</p>
        
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {/* Starter */}
          <div className="bg-white p-8 rounded-2xl shadow-lg">
            <div className="text-sm font-semibold text-blue-600 mb-2">STARTER</div>
            <div className="text-4xl font-bold mb-4">
              ৳2,000<span className="text-lg text-gray-500">/month</span>
            </div>
            <ul className="space-y-3 mb-8">
              <li className="flex items-start gap-2">
                <span className="text-green-500">✓</span>
                <span>Web Hosting (5GB)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500">✓</span>
                <span>10 Marketing Videos/month</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500">✓</span>
                <span>Free SSL</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500">✓</span>
                <span>Email Support</span>
              </li>
            </ul>
            <Link 
              href="/signup?plan=starter" 
              className="block w-full py-3 text-center bg-gray-100 text-gray-800 rounded-lg hover:bg-gray-200 transition"
            >
              Start Trial
            </Link>
          </div>

          {/* Business (Popular) */}
          <div className="bg-gradient-to-br from-purple-600 to-blue-600 text-white p-8 rounded-2xl shadow-xl transform scale-105">
            <div className="text-sm font-semibold mb-2 opacity-90">BUSINESS</div>
            <div className="text-4xl font-bold mb-4">
              ৳3,500<span className="text-lg opacity-75">/month</span>
            </div>
            <ul className="space-y-3 mb-8">
              <li className="flex items-start gap-2">
                <span>✓</span>
                <span>VPS (2 CPU, 4GB RAM)</span>
              </li>
              <li className="flex items-start gap-2">
                <span>✓</span>
                <span>20 Marketing Videos/month</span>
              </li>
              <li className="flex items-start gap-2">
                <span>✓</span>
                <span>Custom Video Topics</span>
              </li>
              <li className="flex items-start gap-2">
                <span>✓</span>
                <span>Priority Support</span>
              </li>
              <li className="flex items-start gap-2">
                <span>✓</span>
                <span>Social Media Scheduler</span>
              </li>
            </ul>
            <Link 
              href="/signup?plan=business" 
              className="block w-full py-3 text-center bg-white text-purple-600 rounded-lg hover:bg-gray-100 transition font-semibold"
            >
              Start Trial →
            </Link>
          </div>

          {/* Enterprise */}
          <div className="bg-white p-8 rounded-2xl shadow-lg">
            <div className="text-sm font-semibold text-purple-600 mb-2">ENTERPRISE</div>
            <div className="text-4xl font-bold mb-4">
              ৳6,000<span className="text-lg text-gray-500">/month</span>
            </div>
            <ul className="space-y-3 mb-8">
              <li className="flex items-start gap-2">
                <span className="text-green-500">✓</span>
                <span>VPS (4 CPU, 8GB RAM) + Storage</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500">✓</span>
                <span>Unlimited Videos</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500">✓</span>
                <span>Custom Branding</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500">✓</span>
                <span>24/7 Support</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500">✓</span>
                <span>We Post For You</span>
              </li>
            </ul>
            <Link 
              href="/signup?plan=enterprise" 
              className="block w-full py-3 text-center bg-gray-100 text-gray-800 rounded-lg hover:bg-gray-200 transition"
            >
              Start Trial
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <div className="max-w-3xl mx-auto bg-gradient-to-r from-blue-600 to-purple-600 rounded-3xl p-12 text-white">
          <h2 className="text-4xl font-bold mb-4">Ready to grow your business?</h2>
          <p className="text-xl mb-8 opacity-90">
            Join 100+ businesses already using Hostamar for hosting + marketing
          </p>
          <Link 
            href="/signup" 
            className="inline-block px-8 py-4 bg-white text-blue-600 text-lg font-semibold rounded-lg hover:bg-gray-100 transition shadow-lg"
          >
            Start Your 7-Day Free Trial →
          </Link>
          <p className="mt-4 text-sm opacity-75">No credit card required. Cancel anytime.</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-8 border-t">
        <div className="flex justify-between items-center text-sm text-gray-600">
          <div>© 2025 Hostamar.com. All rights reserved.</div>
          <div className="flex gap-6">
            <Link href="/terms">Terms</Link>
            <Link href="/privacy">Privacy</Link>
            <Link href="/contact">Contact</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
