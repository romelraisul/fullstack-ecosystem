'use client'

import { useEffect } from 'react'

interface FacebookPagePluginProps {
  href: string
  width?: number
  height?: number
  tabs?: string
  smallHeader?: boolean
  adaptContainerWidth?: boolean
  hideCover?: boolean
  showFacepile?: boolean
}

export function FacebookPagePlugin({
  href,
  width = 340,
  height = 500,
  tabs = 'timeline',
  smallHeader = false,
  adaptContainerWidth = true,
  hideCover = false,
  showFacepile = true,
}: FacebookPagePluginProps) {
  useEffect(() => {
    // Load Facebook SDK
    const loadFbSdk = () => {
      if (typeof window === 'undefined') return
      
      // @ts-ignore
      if (window.FB) {
        // @ts-ignore
        window.FB.XFBML.parse()
        return
      }

      const script = document.createElement('script')
      script.src = "https://connect.facebook.net/en_US/sdk.js#xfbml=1&version=v18.0"
      script.async = true
      script.defer = true
      script.crossOrigin = "anonymous"
      script.onload = () => {
        // @ts-ignore
        if (window.FB) window.FB.XFBML.parse()
      }
      document.body.appendChild(script)
    }

    loadFbSdk()
  }, [])

  return (
    <div className="flex justify-center bg-white rounded-lg shadow-sm overflow-hidden border border-gray-100">
      <div 
        className="fb-page" 
        data-href={href}
        data-tabs={tabs}
        data-width={width}
        data-height={height}
        data-small-header={smallHeader}
        data-adapt-container-width={adaptContainerWidth}
        data-hide-cover={hideCover}
        data-show-facepile={showFacepile}
      >
        <blockquote cite={href} className="fb-xfbml-parse-ignore">
          <a href={href}>Facebook Page</a>
        </blockquote>
      </div>
      <div id="fb-root"></div>
    </div>
  )
}
