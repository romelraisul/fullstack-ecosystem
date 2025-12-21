import { Metadata } from 'next';
import Link from 'next/link';
import { Video, Cloud, Zap, Shield, Users, TrendingUp, Star } from 'lucide-react';

export const metadata: Metadata = {
  title: 'Hostamar - Enterprise Cloud & AI Automation Platform',
  description: 'Scale your business with high-performance hybrid cloud infrastructure and automated AI marketing solutions. Secure, reliable, and built for growth.',
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
            <Link href="/auth/signin" className="px-4 py-2 text-gray-700 hover:text-blue-600 font-medium">
              Login
            </Link>
            <Link 
              href="/contact" 
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium shadow-md"
            >
              Request a Demo
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-24 text-center">
        <div className="max-w-5xl mx-auto">
          <div className="inline-block px-4 py-1.5 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold mb-6">
            🚀 New: Hybrid Cloud Solutions Now Available
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold mb-8 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent leading-tight">
            Enterprise-Grade Hybrid Cloud & <br/> AI-Driven Growth Engines
          </h1>
          <p className="text-xl text-gray-600 mb-10 max-w-3xl mx-auto leading-relaxed">
            Seamlessly integrate on-premise power with cloud scalability. Automate your marketing with AI video generation. Secure, compliant, and engineered for rapid business growth.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <Link 
              href="/contact" 
              className="px-8 py-4 bg-blue-600 text-white text-lg font-bold rounded-xl hover:bg-blue-700 transition shadow-xl hover:shadow-2xl transform hover:-translate-y-1"
            >
              Request a Demo
            </Link>
            <Link 
              href="/auth/signup" 
              className="px-8 py-4 bg-white text-blue-600 text-lg font-bold rounded-xl hover:bg-gray-50 transition border-2 border-blue-600"
            >
              Start Free Trial
            </Link>
          </div>
          
          {/* Trust Badges */}
          <div className="mt-16 flex flex-wrap justify-center gap-8 md:gap-12 text-sm text-gray-500 font-medium">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-green-500" />
              <span>Enterprise Security</span>
            </div>
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5 text-blue-500" />
              <span>500+ Businesses Trusted</span>
            </div>
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-yellow-500" />
              <span>99.99% SLA Uptime</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-20">
        <h2 className="text-4xl font-bold text-center mb-4 text-gray-900">Why Leaders Choose Hostamar</h2>
        <p className="text-center text-gray-600 mb-16 max-w-2xl mx-auto">
          We combine robust infrastructure with cutting-edge AI tools to give you a competitive advantage.
        </p>
        
        <div className="grid md:grid-cols-3 gap-8">
          {/* Feature 1 */}
          <div className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition group">
            <div className="w-14 h-14 bg-blue-100 rounded-xl flex items-center justify-center mb-6 group-hover:bg-blue-600 transition-colors">
              <Cloud className="w-7 h-7 text-blue-600 group-hover:text-white transition-colors" />
            </div>
            <h3 className="text-2xl font-bold mb-3 text-gray-900">Hybrid Cloud Infrastructure</h3>
            <p className="text-gray-600 mb-4">
              Unified management for VPS, RDP, and bare-metal servers. Deploy applications globally with low-latency local execution.
            </p>
            <ul className="text-sm text-gray-500 space-y-2">
              <li className="flex items-center gap-2"><span className="text-green-500">✓</span> Global & Local Nodes</li>
              <li className="flex items-center gap-2"><span className="text-green-500">✓</span> NVMe SSD Storage</li>
              <li className="flex items-center gap-2"><span className="text-green-500">✓</span> Advanced DDoS Protection</li>
            </ul>
          </div>

          {/* Feature 2 */}
          <div className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition border-2 border-purple-100 group relative overflow-hidden">
            <div className="absolute top-0 right-0 bg-purple-600 text-white text-xs font-bold px-3 py-1 rounded-bl-lg">
              AI POWERED
            </div>
            <div className="w-14 h-14 bg-purple-100 rounded-xl flex items-center justify-center mb-6 group-hover:bg-purple-600 transition-colors">
              <Video className="w-7 h-7 text-purple-600 group-hover:text-white transition-colors" />
            </div>
            <h3 className="text-2xl font-bold mb-3 text-gray-900">Automated Content Engine</h3>
            <p className="text-gray-600 mb-4">
              Generate 10+ professional marketing videos weekly tailored to your brand. AI writes scripts, voices overs, and edits for you.
            </p>
            <ul className="text-sm text-gray-500 space-y-2">
              <li className="flex items-center gap-2"><span className="text-green-500">✓</span> AI Script & Voiceover</li>
              <li className="flex items-center gap-2"><span className="text-green-500">✓</span> Multi-Platform Formats</li>
              <li className="flex items-center gap-2"><span className="text-green-500">✓</span> Auto-Posting Scheduler</li>
            </ul>
          </div>

          {/* Feature 3 */}
          <div className="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition group">
            <div className="w-14 h-14 bg-green-100 rounded-xl flex items-center justify-center mb-6 group-hover:bg-green-600 transition-colors">
              <TrendingUp className="w-7 h-7 text-green-600 group-hover:text-white transition-colors" />
            </div>
            <h3 className="text-2xl font-bold mb-3 text-gray-900">Growth Analytics</h3>
            <p className="text-gray-600 mb-4">
              Turn viewers into customers. Track engagement, conversion rates, and ROI across all your infrastructure and campaigns.
            </p>
            <ul className="text-sm text-gray-500 space-y-2">
              <li className="flex items-center gap-2"><span className="text-green-500">✓</span> Real-time Dashboards</li>
              <li className="flex items-center gap-2"><span className="text-green-500">✓</span> Lead Generation Tools</li>
              <li className="flex items-center gap-2"><span className="text-green-500">✓</span> Conversion Tracking</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Testimonials Section (New) */}
      <section className="bg-white py-20 border-t border-gray-100">
        <div className="container mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-16 text-gray-900">Trusted by Innovative Companies</h2>
          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Testimonial 1 */}
            <div className="bg-gray-50 p-8 rounded-2xl relative">
              <div className="flex gap-1 text-yellow-400 mb-4">
                {[...Array(5)].map((_, i) => <Star key={i} className="w-5 h-5 fill-current" />)}
              </div>
              <p className="text-gray-700 text-lg mb-6 italic">
                "Hostamar's hybrid cloud solution allowed us to scale our database operations securely while keeping costs low. The AI video tool is just a massive bonus that doubled our leads."
              </p>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-200 rounded-full flex items-center justify-center font-bold text-blue-700">JS</div>
                <div>
                  <div className="font-bold text-gray-900">John Smith</div>
                  <div className="text-sm text-gray-500">CTO, TechFlow Solutions</div>
                </div>
              </div>
            </div>

            {/* Testimonial 2 */}
            <div className="bg-gray-50 p-8 rounded-2xl relative">
              <div className="flex gap-1 text-yellow-400 mb-4">
                {[...Array(5)].map((_, i) => <Star key={i} className="w-5 h-5 fill-current" />)}
              </div>
              <p className="text-gray-700 text-lg mb-6 italic">
                "We needed a reliable RDP solution for our remote editors. Hostamar delivered high-performance workstations that feel like they are in the same room. Exceptional service."
              </p>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-purple-200 rounded-full flex items-center justify-center font-bold text-purple-700">SJ</div>
                <div>
                  <div className="font-bold text-gray-900">Sarah Jenkins</div>
                  <div className="text-sm text-gray-500">Creative Director, ArtStream</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="container mx-auto px-4 py-20">
        <h2 className="text-4xl font-bold text-center mb-4">Transparent Pricing</h2>
        <p className="text-center text-gray-600 mb-12">Start small, scale infinitely. 7-day free trial included.</p>
        
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {/* Starter */}
          <div className="bg-white p-8 rounded-2xl shadow-lg border border-gray-100 hover:border-blue-200 transition">
            <div className="text-sm font-semibold text-blue-600 mb-2 tracking-wide">STARTER</div>
            <div className="text-4xl font-bold mb-4 text-gray-900">
              ৳2,000<span className="text-lg text-gray-500 font-normal">/mo</span>
            </div>
            <p className="text-gray-500 mb-6 text-sm">Perfect for small businesses starting their digital journey.</p>
            <ul className="space-y-4 mb-8">
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
                <span>Web Hosting (5GB NVMe)</span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
                <span>10 AI Marketing Videos/mo</span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
                <span>Free SSL & Daily Backups</span>
              </li>
            </ul>
            <Link 
              href="/auth/signup?plan=starter" 
              className="block w-full py-3 text-center bg-gray-100 text-gray-800 rounded-lg hover:bg-gray-200 transition font-semibold"
            >
              Start Free Trial
            </Link>
          </div>

          {/* Business (Popular) */}
          <div className="bg-gray-900 text-white p-8 rounded-2xl shadow-2xl transform scale-105 relative">
            <div className="absolute top-0 right-0 bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded-bl-lg">POPULAR</div>
            <div className="text-sm font-semibold mb-2 text-blue-400 tracking-wide">BUSINESS</div>
            <div className="text-4xl font-bold mb-4">
              ৳3,500<span className="text-lg text-gray-400 font-normal">/mo</span>
            </div>
            <p className="text-gray-400 mb-6 text-sm">For growing teams needing power and automation.</p>
            <ul className="space-y-4 mb-8">
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                <span>High-Perf VPS (2 CPU, 4GB)</span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                <span>20 AI Marketing Videos/mo</span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                <span>Social Media Auto-Poster</span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                <span>Priority 24/7 Support</span>
              </li>
            </ul>
            <Link 
              href="/auth/signup?plan=business" 
              className="block w-full py-3 text-center bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-bold"
            >
              Get Started Now
            </Link>
          </div>

          {/* Enterprise */}
          <div className="bg-white p-8 rounded-2xl shadow-lg border border-gray-100 hover:border-purple-200 transition">
            <div className="text-sm font-semibold text-purple-600 mb-2 tracking-wide">ENTERPRISE</div>
            <div className="text-4xl font-bold mb-4 text-gray-900">
              Custom
            </div>
            <p className="text-gray-500 mb-6 text-sm">Tailored solutions for large-scale operations.</p>
            <ul className="space-y-4 mb-8">
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-purple-500 flex-shrink-0" />
                <span>Dedicated Bare Metal Servers</span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-purple-500 flex-shrink-0" />
                <span>Unlimited AI Video Generation</span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-purple-500 flex-shrink-0" />
                <span>Custom Branding & Whitelabel</span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-purple-500 flex-shrink-0" />
                <span>Dedicated Account Manager</span>
              </li>
            </ul>
            <Link 
              href="/contact" 
              className="block w-full py-3 text-center bg-white text-purple-600 border-2 border-purple-600 rounded-lg hover:bg-purple-50 transition font-bold"
            >
              Contact Sales
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <div className="max-w-4xl mx-auto bg-gradient-to-r from-blue-900 to-purple-900 rounded-3xl p-12 text-white shadow-2xl relative overflow-hidden">
          {/* Decorative circles */}
          <div className="absolute top-0 left-0 w-64 h-64 bg-white opacity-5 rounded-full -translate-x-1/2 -translate-y-1/2"></div>
          <div className="absolute bottom-0 right-0 w-64 h-64 bg-white opacity-5 rounded-full translate-x-1/2 translate-y-1/2"></div>
          
          <h2 className="text-4xl font-bold mb-6 relative z-10">Ready to Transform Your Business?</h2>
          <p className="text-xl mb-10 opacity-90 max-w-2xl mx-auto relative z-10">
            Join the hybrid revolution. Secure infrastructure met automated growth. 
            Book a demo today to see it in action.
          </p>
          <div className="flex justify-center gap-4 relative z-10">
            <Link 
              href="/contact" 
              className="inline-block px-8 py-4 bg-white text-blue-900 text-lg font-bold rounded-xl hover:bg-gray-100 transition shadow-lg"
            >
              Request a Demo
            </Link>
            <Link 
              href="/auth/signup" 
              className="inline-block px-8 py-4 bg-transparent border-2 border-white text-white text-lg font-bold rounded-xl hover:bg-white/10 transition"
            >
              Start Free Trial
            </Link>
          </div>
          <p className="mt-6 text-sm opacity-70 relative z-10">No credit card required for trial. Instant setup.</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-12 border-t bg-gray-50">
        <div className="grid md:grid-cols-4 gap-8 mb-8">
          <div className="col-span-1 md:col-span-2">
            <div className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
              Hostamar.com
            </div>
            <p className="text-gray-500 max-w-xs">
              Empowering businesses with next-gen hybrid cloud infrastructure and AI-driven automation tools.
            </p>
          </div>
          <div>
            <h4 className="font-bold text-gray-900 mb-4">Platform</h4>
            <ul className="space-y-2 text-gray-600">
              <li><Link href="/services" className="hover:text-blue-600">Services</Link></li>
              <li><Link href="#pricing" className="hover:text-blue-600">Pricing</Link></li>
              <li><Link href="/auth/signin" className="hover:text-blue-600">Login</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold text-gray-900 mb-4">Company</h4>
            <ul className="space-y-2 text-gray-600">
              <li><Link href="/about" className="hover:text-blue-600">About Us</Link></li>
              <li><Link href="/contact" className="hover:text-blue-600">Contact</Link></li>
              <li><Link href="/privacy" className="hover:text-blue-600">Privacy Policy</Link></li>
              <li><Link href="/terms" className="hover:text-blue-600">Terms of Service</Link></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-200 pt-8 text-center text-sm text-gray-500">
          © 2025 Hostamar.com. All rights reserved.
        </div>
      </footer>
    </div>
  );
}

function CheckCircle2({ className }: { className?: string }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      className={className}
    >
      <circle cx="12" cy="12" r="10" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  )
}

