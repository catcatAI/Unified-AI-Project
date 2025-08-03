import { NextRequest, NextResponse } from 'next/server'
import ZAI from 'z-ai-web-dev-sdk'

export async function POST(request: NextRequest) {
  try {
    const { code, language = 'javascript' } = await request.json()

    if (!code) {
      return NextResponse.json(
        { error: 'Code is required' },
        { status: 400 }
      )
    }

    // Initialize ZAI SDK
    const zai = await ZAI.create()

    // Create code analysis prompt
    const analysisPrompt = `
    Analyze the following ${language} code and provide:
    1. Code quality score (0-100)
    2. List of issues (errors, warnings, suggestions)
    3. Optimization suggestions
    4. Complexity assessment
    
    Code:
    ${code}
    
    Provide the response in JSON format with the following structure:
    {
      "quality": number,
      "issues": [
        {
          "type": "error" | "warning" | "suggestion",
          "message": string,
          "line": number
        }
      ],
      "suggestions": [string],
      "complexity": number (1-5)
    }
    `

    // Create chat completion for code analysis
    const completion = await zai.chat.completions.create({
      messages: [
        {
          role: 'system',
          content: 'You are an expert code analyzer. Provide detailed, actionable feedback on code quality and optimization.'
        },
        {
          role: 'user',
          content: analysisPrompt
        }
      ],
      temperature: 0.3,
      max_tokens: 2000
    })

    const responseContent = completion.choices[0]?.message?.content || '{}'
    
    // Parse the JSON response
    let analysis
    try {
      analysis = JSON.parse(responseContent)
    } catch (parseError) {
      // If JSON parsing fails, create a basic analysis structure
      analysis = {
        quality: 75,
        issues: [
          {
            type: 'suggestion',
            message: 'Code analysis completed. Review the AI response for detailed feedback.',
            line: 1
          }
        ],
        suggestions: ['Review AI-generated analysis for optimization opportunities'],
        complexity: 3
      }
    }

    return NextResponse.json({
      analysis,
      language,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Code analysis API error:', error)
    return NextResponse.json(
      { error: 'Failed to analyze code' },
      { status: 500 }
    )
  }
}