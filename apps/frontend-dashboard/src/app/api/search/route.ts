// API route for web search functionality
import { NextResponse } from 'next/server';
import { apiService } from '@/lib/api';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { query } = body;

    // Forward to backend service
    const response = await apiService.performWebSearch(query);
    
    return NextResponse.json(response);
  } catch (error) {
    console.error('Web search API error:', error);
    return NextResponse.json(
      { error: 'Failed to perform web search' },
      { status: 500 }
    );
  }
}