
import { prisma } from '@/lib/prisma'

export type AnalyticsEvent = 'SIGNUP' | 'LOGIN' | 'VIDEO_GENERATED' | 'PAYMENT_SUCCEEDED' | 'PAYMENT_FAILED' | 'PAGE_VIEW' | 'EMAIL_SENT'

export async function trackEvent(
  userId: string | undefined, 
  event: AnalyticsEvent, 
  metadata?: Record<string, any>
) {
  try {
    console.log(`[Analytics] ${event}:`, { userId, ...metadata })
    
    // In a real production environment, this would push to a dedicated analytics DB (ClickHouse, PostHog)
    // or a specialized table. For MVP, we'll log structured data to stdout for PM2/Datadog to pick up.
    
    // Example: Database persistence (if Analytics model exists)
    /*
    await prisma.analyticsEvent.create({
      data: {
        userId,
        eventType: event,
        metadata: metadata ? JSON.stringify(metadata) : undefined,
      }
    })
    */
  } catch (error) {
    console.error('[Analytics] Failed to track event:', error)
  }
}

export async function getKeyMetrics() {
  try {
    const userCount = await prisma.customer.count()
    // Mocking other metrics for MVP as tables might not exist yet
    return {
      totalUsers: userCount,
      activeSubscriptions: 0,
      monthlyRevenue: 0,
      systemHealth: '99.9%'
    }
  } catch (error) {
    console.error('[Analytics] Failed to fetch metrics:', error)
    return { error: 'Failed to load metrics' }
  }
}
