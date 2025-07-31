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
        const zai = new ZAI.default()
        
        const searchResult = await zai.invokeFunction("web_search", {
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
        
        // 返回模擬搜索結果
        const mockResults = [
          {
            url: 'https://example.com/search-result-1',
            name: 'Mock Search Result 1',
            snippet: 'This is a simulated search result for demonstration purposes.',
            host_name: 'example.com',
            rank: 1,
            date: new Date().toISOString(),
            favicon: ''
          },
          {
            url: 'https://example.com/search-result-2',
            name: 'Mock Search Result 2',
            snippet: 'Another simulated search result showing how the system would work with real search services.',
            host_name: 'example.com',
            rank: 2,
            date: new Date().toISOString(),
            favicon: ''
          }
        ]
        
        return NextResponse.json({
          results: mockResults,
          query,
          num,
          service: 'mock-service',
          timestamp: new Date().toISOString(),
          note: 'These are simulated search results for demonstration purposes'
        })
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