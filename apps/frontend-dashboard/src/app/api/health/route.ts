// API route for health check functionality
import { NextResponse } from 'next/server';
import { apiService } from '@/lib/api';

export async function GET() {
  try {
    // Check backend service health
    const response = await apiService.healthCheck();
    
    return NextResponse.json(response);
  } catch (error) {
    console.error('Health check API error:', error);
    return NextResponse.json(
      { error: 'Backend service is not available' },
      { status: 503 }
    );
  }
}