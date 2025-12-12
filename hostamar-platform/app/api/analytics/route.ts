
import { NextResponse } from 'next/server'
import { getKeyMetrics } from '@/lib/analytics'

export async function GET() {
  const metrics = await getKeyMetrics()
  return NextResponse.json(metrics)
}
