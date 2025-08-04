'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui'
import { Button } from '@acme/ui'
import { Textarea } from '@acme/ui'
import { Badge } from '@acme/ui'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@acme/ui'
import { useToast } from '@/hooks/use-toast'
import { 
  Code, 
  Play, 
  FileText, 
  Bug,
  Lightbulb,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Copy,
  Download
} from 'lucide-react'

interface CodeAnalysis {
  id: string
  language: string
  quality: number
  issues: {
    type: 'error' | 'warning' | 'suggestion'
    message: string
    line?: number
  }[]
  suggestions: string[]
  complexity: number
  timestamp: Date
}

export function CodeAnalysis() {
  const { toast } = useToast()
  const [code, setCode] = useState(`function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

// Calculate the first 10 Fibonacci numbers
for (let i = 0; i < 10; i++) {
  console.log(fibonacci(i));
}`)
  
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysis, setAnalysis] = useState<CodeAnalysis | null>(null)

  const sampleCode = {
    javascript: `function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

// Calculate the first 10 Fibonacci numbers
for (let i = 0; i < 10; i++) {
  console.log(fibonacci(i));
}`,
    python: `def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# Calculate the first 10 Fibonacci numbers
for i in range(10):
    print(fibonacci(i))`,
    react: `import React, { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        Increment
      </button>
    </div>
  );
}`
  }

  const handleAnalyze = async () => {
    if (!code.trim()) return

    setIsAnalyzing(true)

    try {
      const response = await fetch('/api/code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code,
          language: 'javascript'
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to analyze code')
      }

      const data = await response.json()
      
      // Transform API response to match our interface
      const analysis: CodeAnalysis = {
        id: Date.now().toString(),
        language: data.language || 'JavaScript',
        quality: data.analysis.quality || 75,
        issues: data.analysis.issues || [],
        suggestions: data.analysis.suggestions || [],
        complexity: data.analysis.complexity || 3,
        timestamp: new Date()
      }
      
      setAnalysis(analysis)
    } catch (error) {
      console.error('Error analyzing code:', error)
      toast({
        title: "Analysis Error",
        description: "Failed to analyze code. Using fallback analysis.",
        variant: "destructive",
      })
      // Fallback to mock analysis
      const mockAnalysis: CodeAnalysis = {
        id: Date.now().toString(),
        language: 'JavaScript',
        quality: 75,
        issues: [
          {
            type: 'warning',
            message: 'Failed to connect to analysis service. Using fallback analysis.',
            line: 1
          }
        ],
        suggestions: ['Please try again later or check your connection.'],
        complexity: 3,
        timestamp: new Date()
      }
      setAnalysis(mockAnalysis)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const loadSampleCode = (language: keyof typeof sampleCode) => {
    setCode(sampleCode[language])
    setAnalysis(null)
  }

  const getIssueIcon = (type: string) => {
    switch (type) {
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'suggestion':
        return <Lightbulb className="h-4 w-4 text-blue-500" />
      default:
        return <CheckCircle className="h-4 w-4 text-green-500" />
    }
  }

  const getQualityColor = (quality: number) => {
    if (quality >= 80) return 'text-green-600'
    if (quality >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Code Analysis</h1>
          <p className="text-muted-foreground">
            AI-powered code analysis and optimization suggestions
          </p>
        </div>
        <Badge variant="outline">
          <Code className="mr-2 h-4 w-4" />
          Code Analyzer
        </Badge>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Code Input */}
        <Card>
          <CardHeader>
            <CardTitle>Code Editor</CardTitle>
            <CardDescription>
              Paste your code for analysis
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2 mb-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadSampleCode('javascript')}
              >
                JavaScript
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadSampleCode('python')}
              >
                Python
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadSampleCode('react')}
              >
                React
              </Button>
            </div>
            
            <Textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Paste your code here..."
              rows={12}
              className="font-mono text-sm"
            />
            
            <Button
              onClick={handleAnalyze}
              disabled={!code.trim() || isAnalyzing}
              className="w-full"
            >
              {isAnalyzing ? (
                <>
                  Analyzing...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Analyze Code
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Analysis Results */}
        <Card>
          <CardHeader>
            <CardTitle>Analysis Results</CardTitle>
            <CardDescription>
              AI-powered code insights and suggestions
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!analysis ? (
              <div className="text-center py-12">
                <Code className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">No analysis yet</h3>
                <p className="text-muted-foreground">
                  Enter code and click "Analyze Code" to see results
                </p>
              </div>
            ) : (
              <Tabs defaultValue="overview" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="issues">Issues</TabsTrigger>
                  <TabsTrigger value="suggestions">Suggestions</TabsTrigger>
                </TabsList>
                
                <TabsContent value="overview" className="space-y-4">
                  <div className="grid gap-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Code Quality</span>
                      <span className={`text-lg font-bold ${getQualityColor(analysis.quality)}`}>
                        {analysis.quality}%
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Language</span>
                      <Badge variant="outline">{analysis.language}</Badge>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Complexity</span>
                      <div className="flex gap-1">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <div
                            key={i}
                            className={`w-2 h-2 rounded-full ${
                              i < analysis.complexity ? 'bg-primary' : 'bg-muted'
                            }`}
                          />
                        ))}
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Issues Found</span>
                      <span className="text-sm">
                        {analysis.issues.filter(i => i.type === 'error').length} errors, 
                        {analysis.issues.filter(i => i.type === 'warning').length} warnings, 
                        {analysis.issues.filter(i => i.type === 'suggestion').length} suggestions
                      </span>
                    </div>
                  </div>
                </TabsContent>
                
                <TabsContent value="issues" className="space-y-3">
                  {analysis.issues.map((issue, index) => (
                    <div key={index} className="flex items-start gap-3 p-3 rounded-lg border">
                      {getIssueIcon(issue.type)}
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium capitalize">
                            {issue.type}
                          </span>
                          {issue.line && (
                            <Badge variant="outline" className="text-xs">
                              Line {issue.line}
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {issue.message}
                        </p>
                      </div>
                    </div>
                  ))}
                </TabsContent>
                
                <TabsContent value="suggestions" className="space-y-3">
                  {analysis.suggestions.map((suggestion, index) => (
                    <div key={index} className="flex items-start gap-3 p-3 rounded-lg border">
                      <Lightbulb className="h-4 w-4 text-blue-500 mt-0.5" />
                      <p className="text-sm">{suggestion}</p>
                    </div>
                  ))}
                </TabsContent>
              </Tabs>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}