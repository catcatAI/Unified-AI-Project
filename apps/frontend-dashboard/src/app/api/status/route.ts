// API route for system status functionality
import { NextResponse } from 'next/server';
import { apiService } from '@/lib/api';

export async function GET() {
  try {
    // Get system status from backend
    const response = await apiService.getSystemStatus();
    
    return NextResponse.json(response);
  } catch (error) {
    console.error('System status API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch system status' },
      { status: 500 }
    );
  }
}