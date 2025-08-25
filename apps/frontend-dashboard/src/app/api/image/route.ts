// API route for image generation functionality
import { NextResponse } from 'next/server';
import { apiService } from '@/lib/api';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { prompt, size } = body;

    // Forward to backend service
    const response = await apiService.generateImage(prompt, size);
    
    return NextResponse.json(response);
  } catch (error) {
    console.error('Image generation API error:', error);
    return NextResponse.json(
      { error: 'Failed to generate image' },
      { status: 500 }
    );
  }
}