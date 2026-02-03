// API route for chat functionality
import { NextResponse } from 'next/server';
import { apiService } from '@/lib/api';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { message } = body;

    // Forward to backend service
    const response = await apiService.sendChatMessage(message);
    
    return NextResponse.json(response);
  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { error: 'Failed to process chat message' },
      { status: 500 }
    );
  }
}