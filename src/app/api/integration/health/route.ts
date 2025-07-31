import { NextRequest, NextResponse } from 'next/server'
import { getIntegrationBridge } from '@/lib/integration-bridge'

export async function GET(request: NextRequest) {
  try {
    const bridge = getIntegrationBridge()
    const statuses = bridge.getAllServiceStatuses()

    // 計算整體系統健康狀態
    const onlineServices = statuses.filter(s => s.status === 'online').length
    const totalServices = statuses.length
    const healthPercentage = totalServices > 0 ? (onlineServices / totalServices) * 100 : 0

    const systemHealth = {
      overall: healthPercentage >= 80 ? 'healthy' : healthPercentage >= 50 ? 'degraded' : 'unhealthy',
      percentage: Math.round(healthPercentage),
      services: statuses,
      timestamp: new Date().toISOString()
    }

    return NextResponse.json(systemHealth)
  } catch (error) {
    console.error('Integration health check failed:', error)
    return NextResponse.json(
      { 
        error: 'Failed to check integration health',
        overall: 'unhealthy',
        percentage: 0,
        services: [],
        timestamp: new Date().toISOString()
      },
      { status: 500 }
    )
  }
}