import { NextRequest, NextResponse } from 'next/server'
import { getIntegrationBridge } from '@/lib/integration-bridge'

export async function POST(request: NextRequest) {
  try {
    const { query, num = 10 } = await request.json()

    if (!query) {
      return NextResponse.json(
        { error: 'Query is required' },
        { status: 400 }
      )
    }

    const bridge = getIntegrationBridge()
    
    try {
      const response = await bridge.webSearch(query, num)
      
      return NextResponse.json({
        results: response.results || response,
        query,
        num: response.num || num,
        service: response.service || 'ai-dashboard',
        timestamp: new Date().toISOString()
      })
    } catch (searchError) {
      console.warn('Primary search service failed, trying fallback:', searchError)
      
      // 嘗試直接使用z-ai-web-dev-sdk
      try {
        const ZAI = await import('z-ai-web-dev-sdk')
        const zai = await ZAI.create()
        
        const searchResult = await zai.functions.invoke("web_search", {
          query,
          num
        })

        return NextResponse.json({
          results: searchResult,
          query,
          num,
          service: 'z-ai-sdk',
          timestamp: new Date().toISOString()
        })
      } catch (fallbackError) {
        console.error('Fallback search service also failed:', fallbackError)
        return NextResponse.json(
          { 
            error: 'Web search services are currently unavailable',
            query,
            num,
            timestamp: new Date().toISOString()
          },
          { status: 503 }
        )
      }
    }

  } catch (error) {
    console.error('Unified web search API error:', error)
    return NextResponse.json(
      { error: 'Failed to perform web search' },
      { status: 500 }
    )
  }
}