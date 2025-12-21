'use client'

import { Facebook, Twitter, Linkedin, Link as LinkIcon, Check } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/Button'

interface ShareButtonsProps {
  url: string
  title: string
}

export function ShareButtons({ url, title }: ShareButtonsProps) {
  const [copied, setCopied] = useState(false)

  const shareUrls = {
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
    twitter: `https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title)}`,
    linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`,
  }

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className="flex flex-wrap gap-2 items-center">
      <span className="text-sm font-medium text-gray-500 mr-2">Share:</span>
      
      <a href={shareUrls.facebook} target="_blank" rel="noopener noreferrer">
        <Button variant="outline" size="sm" className="bg-[#1877F2] text-white hover:bg-[#166fe5] border-none">
          <Facebook className="w-4 h-4" />
        </Button>
      </a>

      <a href={shareUrls.twitter} target="_blank" rel="noopener noreferrer">
        <Button variant="outline" size="sm" className="bg-[#1DA1F2] text-white hover:bg-[#1a91da] border-none">
          <Twitter className="w-4 h-4" />
        </Button>
      </a>

      <a href={shareUrls.linkedin} target="_blank" rel="noopener noreferrer">
        <Button variant="outline" size="sm" className="bg-[#0A66C2] text-white hover:bg-[#0958ae] border-none">
          <Linkedin className="w-4 h-4" />
        </Button>
      </a>

      <Button 
        variant="outline" 
        size="sm" 
        onClick={copyToClipboard}
        className={copied ? "text-green-600 border-green-600" : ""}
      >
        {copied ? <Check className="w-4 h-4" /> : <LinkIcon className="w-4 h-4" />}
      </Button>
    </div>
  )
}
