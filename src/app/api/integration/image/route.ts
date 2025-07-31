import { NextRequest, NextResponse } from 'next/server'
import { getIntegrationBridge } from '@/lib/integration-bridge'

export async function POST(request: NextRequest) {
  try {
    const { prompt, size = '1024x1024' } = await request.json()

    if (!prompt) {
      return NextResponse.json(
        { error: 'Prompt is required' },
        { status: 400 }
      )
    }

    const bridge = getIntegrationBridge()
    
    try {
      const response = await bridge.generateImage(prompt, size)
      
      return NextResponse.json({
        image: response.image,
        prompt,
        size: response.size || size,
        service: response.service || 'ai-dashboard',
        timestamp: new Date().toISOString()
      })
    } catch (imageError) {
      console.warn('Primary image service failed, trying fallback:', imageError)
      
      // 嘗試直接使用z-ai-web-dev-sdk
      try {
        const ZAI = await import('z-ai-web-dev-sdk')
        const zai = new ZAI.default()
        
        const imageResponse = await zai.createImageGeneration({
          prompt,
          size
        })

        const imageBase64 = imageResponse.data[0].base64

        return NextResponse.json({
          image: imageBase64,
          prompt,
          size,
          service: 'z-ai-sdk',
          timestamp: new Date().toISOString()
        })
      } catch (fallbackError) {
        console.error('Fallback image service also failed:', fallbackError)
        
        // 返回模擬圖像響應
        const mockImageBase64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
        
        return NextResponse.json({
          image: mockImageBase64,
          prompt,
          size,
          service: 'mock-service',
          timestamp: new Date().toISOString(),
          note: 'This is a simulated 1x1 pixel image for demonstration purposes'
        })
      }
    }

  } catch (error) {
    console.error('Unified image generation API error:', error)
    return NextResponse.json(
      { error: 'Failed to generate image' },
      { status: 500 }
    )
  }
}