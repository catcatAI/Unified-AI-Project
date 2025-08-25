// API route for code analysis functionality
import { NextResponse } from 'next/server';
import { apiService } from '@/lib/api';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { code, language } = body;

    // Forward to backend service
    const response = await apiService.analyzeCode(code, language);
    
    return NextResponse.json(response);
  } catch (error) {
    console.error('Code analysis API error:', error);
    return NextResponse.json(
      { error: 'Failed to analyze code' },
      { status: 500 }
    );
  }
}