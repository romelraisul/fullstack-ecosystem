'use client'

import { useState } from 'react'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { Mail, MapPin, Phone } from 'lucide-react'
import { FacebookPagePlugin } from '@/components/social/FacebookPagePlugin'

export default function ContactPage() {
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Mock submission
    setSubmitted(true)
  }

  return (
    <div className="container mx-auto px-4 py-16">
      <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-12">
        
        {/* Contact Info */}
        <div>
          <h1 className="text-4xl font-bold mb-6 text-gray-900">Let's Talk Business</h1>
          <p className="text-gray-600 mb-8">
            Ready to request a demo or need a custom infrastructure plan? Our team of experts is ready to help you scale.
          </p>
          
          <div className="space-y-6 mb-10">
            <div className="flex items-start gap-4">
              <Mail className="w-6 h-6 text-blue-600 mt-1" />
              <div>
                <h3 className="font-semibold text-gray-900">Email</h3>
                <p className="text-gray-600">support@hostamar.com</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <Phone className="w-6 h-6 text-blue-600 mt-1" />
              <div>
                <h3 className="font-semibold text-gray-900">Phone</h3>
                <p className="text-gray-600">+880 1700-000000</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <MapPin className="w-6 h-6 text-blue-600 mt-1" />
              <div>
                <h3 className="font-semibold text-gray-900">Office</h3>
                <p className="text-gray-600">Dhaka, Bangladesh</p>
              </div>
            </div>
          </div>

          {/* Social Widget */}
          <div className="mt-8">
            <h3 className="font-semibold text-gray-900 mb-4">Connect with us on Facebook</h3>
            <FacebookPagePlugin href="https://www.facebook.com/share/17R9R19AyA/" />
          </div>
        </div>

        {/* Contact Form */}
        <div className="bg-white p-8 rounded-2xl shadow-lg border border-gray-100">
          {submitted ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">✅</span>
              </div>
              <h3 className="text-xl font-bold text-gray-900">Message Sent!</h3>
              <p className="text-gray-600 mt-2">We'll get back to you shortly.</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              <Input label="Name" placeholder="Your Name" required />
              <Input label="Email" type="email" placeholder="you@example.com" required />
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Message</label>
                <textarea 
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none min-h-[150px]"
                  placeholder="How can we help you?"
                  required
                ></textarea>
              </div>
              <Button className="w-full">Send Message</Button>
            </form>
          )}
        </div>

      </div>
    </div>
  )
}
