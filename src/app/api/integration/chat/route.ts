import { NextRequest, NextResponse } from 'next/server'
import { getIntegrationBridge } from '@/lib/integration-bridge'

export async function POST(request: NextRequest) {
  try {
    const { message, model = 'gpt-4', userId = 'dashboard_user', sessionId = 'dashboard_session' } = await request.json()

    if (!message) {
      return NextResponse.json(
        { error: 'Message is required' },
        { status: 400 }
      )
    }

    const bridge = getIntegrationBridge()
    
    // 嘗試使用統一的AI聊天服務
    try {
      const response = await bridge.sendAIChat(message, model)
      
      return NextResponse.json({
        response: response.response_text || response.response || 'No response generated',
        model: response.model || model,
        service: response.service || 'unified-ai',
        userId,
        sessionId,
        timestamp: new Date().toISOString()
      })
    } catch (aiError) {
      console.warn('Primary AI service failed, trying fallback:', aiError)
      
      // 如果主要服務失敗，嘗試直接使用z-ai-web-dev-sdk
      try {
        const ZAI = await import('z-ai-web-dev-sdk')
        const zai = new ZAI.default({
          baseUrl: 'http://localhost:8080',
          apiKey: 'test-key'
        })
        
        const completion = await zai.createChatCompletion({
          messages: [
            {
              role: 'system',
              content: 'You are a helpful AI assistant integrated into a unified AI dashboard. Provide helpful, accurate, and concise responses.'
            },
            {
              role: 'user',
              content: message
            }
          ],
          temperature: 0.7,
          max_tokens: 1000
        })

        const response = completion.choices[0]?.message?.content || 'No response generated'

        return NextResponse.json({
          response,
          model,
          service: 'z-ai-sdk',
          userId,
          sessionId,
          timestamp: new Date().toISOString()
        })
      } catch (fallbackError) {
        console.error('Fallback AI service also failed:', fallbackError)
        
        // 返回模擬響應以保持系統運行
        const mockResponse = `I understand you said: "${message}". This is a simulated response as the AI services are currently being configured. In a production environment, this would connect to actual AI models.`
        
        return NextResponse.json({
          response: mockResponse,
          model,
          service: 'mock-service',
          userId,
          sessionId,
          timestamp: new Date().toISOString(),
          note: 'This is a simulated response for demonstration purposes'
        })
      }
    }

  } catch (error) {
    console.error('Unified chat API error:', error)
    return NextResponse.json(
      { error: 'Failed to process chat request' },
      { status: 500 }
    )
  }
}