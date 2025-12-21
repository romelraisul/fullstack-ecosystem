import type { Metadata } from 'next'
import { 
  Monitor, 
  Video, 
  Globe, 
  Database, 
  HardDrive, 
  MessageSquare, 
  ShieldCheck, 
  Gamepad2, 
  Smartphone, 
  RefreshCcw,
  CheckCircle2
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import Link from 'next/link'
import { ShareButtons } from '@/components/social/ShareButtons'

export const metadata: Metadata = {
  title: 'Cloud & AI Services | Hostamar',
  description: 'Explore our high-performance RDP, VPS, AI marketing automation, and managed database services tailored for growth.',
}

const services = [
  {
    title: "High-Performance RDP",
    description: "Experience lag-free remote work with dedicated Windows environments on residential IPs. Perfect for managing international accounts securely without bans.",
    icon: Monitor,
    features: ["Dedicated Residential IP", "NVMe Storage", "4-8GB RAM / 2 vCPU", "Secure RDP Access"]
  },
  {
    title: "AI Video Marketing Workstations",
    description: "Automate your content creation. Our GPU-accelerated workstations come pre-configured with AI tools to generate, edit, and render 4K video content at scale.",
    icon: Video,
    features: ["NVIDIA GPU Passthrough", "Pre-installed AI Tools", "Ryzen 9000 Series CPU", "Automated Rendering Pipelines"]
  },
  {
    title: "Managed Cloud Hosting",
    description: "Focus on your business, not servers. Our containerized hosting powered by OpenLiteSpeed ensures your website loads instantly and handles traffic spikes effortlessly.",
    icon: Globe,
    features: ["LXC Container Technology", "CyberPanel Control Panel", "Free SSL Certificates", "Daily Offsite Backups"]
  },
  {
    title: "Database-as-a-Service (DBaaS)",
    description: "Deploy production-ready databases in seconds. Highly available PostgreSQL, MongoDB, or Redis instances managed via Portainer for complete control.",
    icon: Database,
    features: ["Dockerized Instances", "Automated Dumps to S3", "Portainer Management", "High Availability Clusters"]
  },
  {
    title: "S3-Compatible Object Storage",
    description: "Slash your storage costs with our secure, local object storage. Fully compatible with Amazon S3 API, ideal for backups, media archives, and data lakes.",
    icon: HardDrive,
    features: ["S3 API Compatible (MinIO)", "ZFS Data Integrity", "Redundant Storage", "Cost-Effective Archiving"]
  },
  {
    title: "Telegram Bot Hosting",
    description: "Keep your business running 24/7 with reliable bot hosting. Automate customer support, order tracking, and notifications with zero downtime.",
    icon: MessageSquare,
    features: ["24/7 Uptime", "Python/Node.js Support", "Payment Automation Capable", "Scalable Resources"]
  },
  {
    title: "Privacy & VPN Solutions",
    description: "Protect your business data and browse anonymously. Our WireGuard-based VPNs with AdGuard filtering block trackers and ensure secure remote access.",
    icon: ShieldCheck,
    features: ["WireGuard VPN", "AdGuard DNS Filtering", "Tracker Blocking", "Family/Business Safety Controls"]
  },
  {
    title: "Low Latency Game Servers",
    description: "Dominate the competition with high-tick-rate servers. BDIX connectivity ensures minimal ping for Minecraft, CS2, or Valorant matches.",
    icon: Gamepad2,
    features: ["High Clock Speed CPUs", "BDIX Connectivity (Local)", "DDoS Protection", "Instant Setup"]
  },
  {
    title: "Mobile App Testing Farm",
    description: "Ship bug-free apps faster. Test your Android applications across multiple OS versions in real-time directly from your browser without owning devices.",
    icon: Smartphone,
    features: ["Android 9-12 Support", "Browser-Based Access", "Real Device Emulation", "ADB Debugging"]
  },
  {
    title: "Offsite Backup & Disaster Recovery",
    description: "Insurable protection for your critical data. Secure, encrypted remote backups ensure your business survives ransomware or hardware failures.",
    icon: RefreshCcw,
    features: ["End-to-End Encryption", "UrBackup / Syncthing", "Automated Scheduling", "Ransomware Protection"]
  }
]

export default function ServicesPage() {
  return (
    <div className="bg-white">
      {/* Hero Section */}
      <div className="bg-gray-50 border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-16 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl tracking-tight mb-4">
            Solutions Engineered for Growth
          </h1>
          <p className="max-w-2xl mx-auto text-xl text-gray-500 mb-8">
            From freelancers to enterprises, Hostamar provides the high-performance infrastructure you need to scale.
          </p>
          <div className="flex justify-center">
            <ShareButtons url="https://hostamar.com/services" title="Check out Hostamar's Cloud & AI Services" />
          </div>
        </div>
      </div>

      {/* Services Grid */}
      <div className="max-w-7xl mx-auto px-4 py-16 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {services.map((service, index) => (
            <div 
              key={index}
              className="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow p-8 flex flex-col"
            >
              <div className="bg-blue-50 w-14 h-14 rounded-xl flex items-center justify-center mb-6">
                <service.icon className="w-7 h-7 text-blue-600" />
              </div>
              
              <h3 className="text-xl font-bold text-gray-900 mb-3">
                {service.title}
              </h3>
              
              <p className="text-gray-600 mb-6 flex-grow">
                {service.description}
              </p>
              
              <ul className="space-y-3 mb-8">
                {service.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                    <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <Link href="/contact" className="mt-auto">
                <Button variant="outline" className="w-full hover:bg-blue-50 hover:text-blue-600 hover:border-blue-200 transition-colors">
                  Request Info
                </Button>
              </Link>
            </div>
          ))}
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-blue-600">
        <div className="max-w-7xl mx-auto px-4 py-16 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to upgrade your infrastructure?
          </h2>
          <p className="text-blue-100 text-lg mb-8 max-w-2xl mx-auto">
            Contact our sales team to get a custom quote tailored to your specific business needs.
          </p>
          <div className="flex justify-center gap-4">
            <Link href="/contact">
              <Button size="lg" className="bg-white text-blue-600 hover:bg-gray-100 border-none font-bold">
                Request a Demo
              </Button>
            </Link>
            <Link href="/auth/signup">
              <Button size="lg" variant="outline" className="text-white border-white hover:bg-blue-700">
                Create Account
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
