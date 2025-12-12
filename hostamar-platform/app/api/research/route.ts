import { NextResponse } from 'next/server'
import { trackEvent } from '@/lib/analytics'

const GEMINI_API_KEY = process.env.GEMINI_API_KEY
const API_BASE = 'https://generativelanguage.googleapis.com/v1beta/interactions'

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { query } = body

    if (!query) {
      return NextResponse.json({ error: 'Query is required' }, { status: 400 })
    }

    await trackEvent(undefined, 'PAGE_VIEW', { page: 'api/research', query })

    console.log(`[Deep Research] Processing: ${query}`)

    if (!GEMINI_API_KEY) {
      console.warn('GEMINI_API_KEY not set. Returning mock data.')
      return NextResponse.json({ 
        status: 'completed', 
        report: getMockReport(query),
        timestamp: new Date().toISOString(),
        mock: true
      })
    }

    // 1. Start Interaction
    const startResponse = await fetch(`${API_BASE}?key=${GEMINI_API_KEY}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent: 'deep-research-pro-preview-12-2025',
        input: query,
        background: true
      })
    })

    if (!startResponse.ok) {
      const err = await startResponse.text()
      console.error('Gemini API Error:', err)
      // Fallback to mock if API fails (e.g., model not found in preview)
      return NextResponse.json({ 
        status: 'completed', 
        report: getMockReport(query), 
        error: 'API_FAIL_FALLBACK',
        details: err 
      })
    }

    const startData = await startResponse.json()
    const interactionId = startData.name // e.g., "interactions/..."

    // 2. Poll for completion (Simplified: Wait up to 10s then return "In Progress" or result)
    // In a real app, we'd return the ID and let the frontend poll.
    // For this MVP, we'll wait a bit to see if it's quick, otherwise return the ID.
    
    let report = null
    let status = 'in_progress'
    
    // Quick poll check (just one for now to demonstrate logic)
    // Real implementation requires a separate polling route or WebSocket
    
    return NextResponse.json({
      status: 'initiated',
      interactionId: interactionId,
      message: 'Research started. Check back later.',
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Research API Error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

function getMockReport(query: string) {
  return `
# Market Insight: ${query}
**(Mock Data - Set GEMINI_API_KEY for real insights)**

## Executive Summary
Analysis indicates strong potential in this sector.

## Key Data Points
- **Trend:** Positive growth signal.
- **Competition:** Moderate.
- **Opportunity:** High demand for specialized services.

## Strategic Recommendation
Invest in this area immediately to capture early market share.
`
}