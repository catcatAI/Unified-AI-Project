'use client'

import { useState } from 'react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  Code, 
  FileText, 
  AlertTriangle,
  CheckCircle,
  Loader2,
  Copy,
  Download
} from 'lucide-react'

interface CodeAnalysisResult {
  quality: number
  issues: Array<{
    type: 'error' | 'warning' | 'info'
    message: string
    line: number
    suggestion?: string
  }>
  suggestions: string[]
  complexity: {
    score: number
    level: 'low' | 'medium' | 'high'
  }
  metrics: {
    lines: number
    functions: number
    complexity: number
    maintainability: number
  }
}

const languageOptions = [
  { value: 'javascript', label: 'JavaScript' },
  { value: 'typescript', label: 'TypeScript' },
  { value: 'python', label: 'Python' },
  { value: 'java', label: 'Java' },
  { value: 'cpp', label: 'C++' }
]

const sampleCode = {
  javascript: `function calculateSum(a, b) {
  // This function calculates the sum of two numbers
  return a + b;
}

function processData(data) {
  if (!data || data.length === 0) {
    return null;
  }
  
  let result = [];
  for (let i = 0; i < data.length; i++) {
    result.push(data[i] * 2);
  }
  
  return result;
}`,
  python: `def calculate_sum(a, b):
    """This function calculates the sum of two numbers"""
    return a + b

def process_data(data):
    """Process a list of data by multiplying each element by 2"""
    if not data:
        return None
    
    result = []
    for item in data:
        result.append(item * 2)
    
    return result`
}

export function UnifiedCodeAnalysis() {
  const [code, setCode] = useState(sampleCode.javascript)
  const [selectedLanguage, setSelectedLanguage] = useState('javascript')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<CodeAnalysisResult | null>(null)

  const handleAnalyze = async () => {
    if (!code.trim() || isAnalyzing) return

    setIsAnalyzing(true)
    
    // 模擬分析過程
    setTimeout(() => {
      const mockResult: CodeAnalysisResult = {
        quality: 85,
        issues: [
          {
            type: 'warning',
            message: '考慮添加輸入驗證',
            line: 1,
            suggestion: '添加類型檢查和邊界條件驗證'
          },
          {
            type: 'info',
            message: '可以使用更現代的數組方法',
            line: 9,
            suggestion: '考慮使用 map() 方法替代 for 循環'
          }
        ],
        suggestions: [
          '添加 JSDoc 註釋以提高代碼可讀性',
          '考慮使用 TypeScript 進行類型安全',
          '添加單元測試以確保代碼質量'
        ],
        complexity: {
          score: 3,
          level: 'low'
        },
        metrics: {
          lines: 15,
          functions: 2,
          complexity: 3,
          maintainability: 85
        }
      }
      
      setAnalysisResult(mockResult)
      setIsAnalyzing(false)
    }, 2000)
  }

  const useSampleCode = () => {
    const sample = sampleCode[selectedLanguage as keyof typeof sampleCode]
    if (sample) {
      setCode(sample)
    }
  }

  const clearCode = () => {
    setCode('')
    setAnalysisResult(null)
  }

  const getQualityColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getQualityBadge = (score: number) => {
    if (score >= 80) return 'default'
    if (score >= 60) return 'secondary'
    return 'destructive'
  }

  const getComplexityColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600'
      case 'medium': return 'text-yellow-600'
      case 'high': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  const getIssueIcon = (type: string) => {
    switch (type) {
      case 'error': return <AlertTriangle className="h-4 w-4 text-red-500" />
      case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case 'info': return <CheckCircle className="h-4 w-4 text-blue-500" />
      default: return null
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">代碼分析</h1>
          <p className="text-muted-foreground">
            多語言代碼質量分析與優化建議
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Badge variant="outline">
            語言: {languageOptions.find(l => l.value === selectedLanguage)?.label}
          </Badge>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Code Input */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Code className="h-5 w-5" />
                代碼輸入
              </CardTitle>
              <CardDescription>
                輸入要分析的代碼
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">編程語言</label>
                <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {languageOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">代碼</label>
                <Textarea
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="輸入要分析的代碼..."
                  className="min-h-[300px] font-mono text-sm"
                  disabled={isAnalyzing}
                />
              </div>

              <div className="flex gap-2">
                <Button 
                  onClick={handleAnalyze}
                  disabled={!code.trim() || isAnalyzing}
                  className="flex-1"
                >
                  {isAnalyzing ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      分析中...
                    </>
                  ) : (
                    <>
                      <Code className="h-4 w-4 mr-2" />
                      分析代碼
                    </>
                  )}
                </Button>
                
                <Button variant="outline" onClick={useSampleCode}>
                  <FileText className="h-4 w-4 mr-2" />
                  示例
                </Button>
                
                <Button variant="outline" onClick={clearCode}>
                  清除
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Analysis Results */}
        <div className="space-y-4">
          {isAnalyzing && (
            <Card>
              <CardContent className="flex items-center justify-center h-64">
                <div className="text-center">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
                  <p className="text-muted-foreground">正在分析代碼...</p>
                </div>
              </CardContent>
            </Card>
          )}

          {!isAnalyzing && !analysisResult && (
            <Card>
              <CardContent className="flex items-center justify-center h-64">
                <div className="text-center">
                  <Code className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">
                    等待代碼分析
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    輸入代碼並點擊分析按鈕
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {analysisResult && (
            <>
              {/* Quality Score */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <CheckCircle className="h-5 w-5" />
                      代碼質量評分
                    </span>
                    <Badge variant={getQualityBadge(analysisResult.quality)}>
                      {analysisResult.quality}/100
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">整體質量</span>
                      <span className={`font-medium ${getQualityColor(analysisResult.quality)}`}>
                        {analysisResult.quality >= 80 ? '優秀' :
                         analysisResult.quality >= 60 ? '良好' : '需要改進'}
                      </span>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>複雜度</span>
                        <span className={getComplexityColor(analysisResult.complexity.level)}>
                          {analysisResult.complexity.level === 'low' ? '低' :
                           analysisResult.complexity.level === 'medium' ? '中' : '高'}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>可維護性</span>
                        <span>{analysisResult.metrics.maintainability}%</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Issues */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5" />
                    發現的問題 ({analysisResult.issues.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {analysisResult.issues.map((issue, index) => (
                      <div key={index} className="p-3 border rounded-lg">
                        <div className="flex items-start gap-2">
                          {getIssueIcon(issue.type)}
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-sm font-medium">
                                第 {issue.line} 行
                              </span>
                              <Badge variant={
                                issue.type === 'error' ? 'destructive' :
                                issue.type === 'warning' ? 'secondary' : 'default'
                              }>
                                {issue.type === 'error' ? '錯誤' :
                                 issue.type === 'warning' ? '警告' : '信息'}
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground mb-2">
                              {issue.message}
                            </p>
                            {issue.suggestion && (
                              <p className="text-sm text-blue-600">
                                💡 {issue.suggestion}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Suggestions */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    優化建議
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {analysisResult.suggestions.map((suggestion, index) => (
                      <div key={index} className="flex items-start gap-2">
                        <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                        <span className="text-sm">{suggestion}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  )
}