'use client'

import Link from 'next/link'
import { useState } from 'react'
import { Menu, X, Cloud } from 'lucide-react'
import { Button } from '../ui/Button'

export function Navbar() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <nav className="bg-white border-b border-gray-100 sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <Cloud className="h-8 w-8 text-blue-600" />
            <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Hostamar
            </span>
          </Link>

          {/* Desktop Menu */}
          <div className="hidden md:flex items-center gap-8">
            <Link href="/about" className="text-gray-600 hover:text-blue-600 font-medium">About</Link>
            <Link href="/features" className="text-gray-600 hover:text-blue-600 font-medium">Features</Link>
            <Link href="/services" className="text-gray-600 hover:text-blue-600 font-medium">Services</Link>
            <Link href="/pricing" className="text-gray-600 hover:text-blue-600 font-medium">Pricing</Link>
            <Link href="/contact" className="text-gray-600 hover:text-blue-600 font-medium">Contact</Link>
          </div>

          {/* Auth Buttons */}
          <div className="hidden md:flex items-center gap-4">
            <Link href="/auth/signin">
              <Button variant="ghost" size="sm">Log in</Button>
            </Link>
            <Link href="/auth/signup">
              <Button size="sm">Get Started</Button>
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button 
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            {isOpen ? <X /> : <Menu />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden border-t border-gray-100 bg-white absolute w-full shadow-lg">
          <div className="p-4 space-y-4">
            <Link href="/about" className="block text-gray-600 py-2">About</Link>
            <Link href="/features" className="block text-gray-600 py-2">Features</Link>
            <Link href="/services" className="block text-gray-600 py-2">Services</Link>
            <Link href="/pricing" className="block text-gray-600 py-2">Pricing</Link>
            <Link href="/contact" className="block text-gray-600 py-2">Contact</Link>
            <div className="pt-4 border-t border-gray-100 flex flex-col gap-3">
              <Link href="/auth/signin" className="w-full">
                <Button variant="outline" className="w-full">Log in</Button>
              </Link>
              <Link href="/auth/signup" className="w-full">
                <Button className="w-full">Get Started</Button>
              </Link>
            </div>
          </div>
        </div>
      )}
    </nav>
  )
}
