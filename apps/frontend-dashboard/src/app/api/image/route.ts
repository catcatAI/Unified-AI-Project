import { NextRequest, NextResponse } from 'next/server'
import ZAI from 'z-ai-web-dev-sdk'

export async function POST(request: NextRequest) {
  try {
    const { prompt, size = '1024x1024' } = await request.json()

    if (!prompt) {
      return NextResponse.json(
        { error: 'Prompt is required' },
        { status: 400 }
      )
    }

    // Initialize ZAI SDK
    const zai = await ZAI.create()

    // Generate image
    const response = await zai.images.generations.create({
      prompt,
      size
    })

    // Get the base64 encoded image data
    const imageBase64 = response.data[0].base64

    return NextResponse.json({
      image: imageBase64,
      prompt,
      size,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Image generation API error:', error)
    return NextResponse.json(
      { error: 'Failed to generate image' },
      { status: 500 }
    )
  }
}