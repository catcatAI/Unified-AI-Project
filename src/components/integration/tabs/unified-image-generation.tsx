'use client'

import { useState, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  Image as ImageIcon, 
  Download, 
  Loader2,
  Sparkles,
  Copy,
  RefreshCw,
  AlertCircle,
  CheckCircle
} from 'lucide-react'

interface GeneratedImage {
  id: string
  prompt: string
  imageData: string
  size: string
  service: string
  timestamp: Date
  status: 'generating' | 'completed' | 'error'
}

const sizeOptions = [
  { value: '256x256', label: '256×256 (小)' },
  { value: '512x512', label: '512×512 (中)' },
  { value: '1024x1024', label: '1024×1024 (大)' }
]

const promptExamples = [
  '一個可愛的貓咪在花園中玩耍',
  '未來主義的城市景觀，霓虹燈閃爍',
  '美麗的山水畫，有山有水有雲',
  '抽象藝術，色彩繽紛的幾何圖形',
  '溫馨的咖啡館內景，有書籍和咖啡'
]

export function UnifiedImageGeneration() {
  const [prompt, setPrompt] = useState('')
  const [selectedSize, setSelectedSize] = useState('1024x1024')
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedImages, setGeneratedImages] = useState<GeneratedImage[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleGenerateImage = async () => {
    if (!prompt.trim() || isGenerating) return

    const newImage: GeneratedImage = {
      id: Date.now().toString(),
      prompt,
      imageData: '',
      size: selectedSize,
      service: 'unified-ai',
      timestamp: new Date(),
      status: 'generating'
    }

    setGeneratedImages(prev => [newImage, ...prev])
    setIsGenerating(true)

    try {
      const response = await fetch('/api/integration/image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt,
          size: selectedSize
        })
      })

      const data = await response.json()

      if (response.ok) {
        setGeneratedImages(prev => prev.map(img => 
          img.id === newImage.id 
            ? {
                ...img,
                imageData: data.image,
                service: data.service,
                status: 'completed'
              }
            : img
        ))
      } else {
        throw new Error(data.error || 'Failed to generate image')
      }
    } catch (error) {
      console.error('Image generation error:', error)
      
      setGeneratedImages(prev => prev.map(img => 
        img.id === newImage.id 
          ? { ...img, status: 'error' }
          : img
      ))
    } finally {
      setIsGenerating(false)
    }
  }

  const downloadImage = (imageData: string, filename: string) => {
    const link = document.createElement('a')
    link.href = `data:image/png;base64,${imageData}`
    link.download = filename
    link.click()
  }

  const copyPrompt = (promptText: string) => {
    navigator.clipboard.writeText(promptText)
  }

  const applyExamplePrompt = (examplePrompt: string) => {
    setPrompt(examplePrompt)
  }

  const clearHistory = () => {
    setGeneratedImages([])
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'generating':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return null
    }
  }

  const formatTime = (date: Date) => {
    return date.toLocaleString('zh-TW')
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">圖像生成</h1>
          <p className="text-muted-foreground">
            使用AI生成高質量圖像
          </p>
        </div>
        
        <Button variant="outline" onClick={clearHistory} disabled={generatedImages.length === 0}>
          <RefreshCw className="h-4 w-4 mr-2" />
          清除歷史
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Generation Panel */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                圖像生成
              </CardTitle>
              <CardDescription>
                輸入描述來生成圖像
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">描述提示詞</label>
                <Textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="描述您想要生成的圖像..."
                  className="min-h-[100px]"
                  disabled={isGenerating}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">圖像尺寸</label>
                <Select value={selectedSize} onValueChange={setSelectedSize} disabled={isGenerating}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {sizeOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Button 
                onClick={handleGenerateImage}
                disabled={!prompt.trim() || isGenerating}
                className="w-full"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    生成中...
                  </>
                ) : (
                  <>
                    <ImageIcon className="h-4 w-4 mr-2" />
                    生成圖像
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">示例提示詞</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {promptExamples.map((example, index) => (
                <div
                  key={index}
                  className="p-2 rounded border cursor-pointer hover:border-primary/50 transition-colors"
                  onClick={() => applyExamplePrompt(example)}
                >
                  <div className="text-sm">{example}</div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Generated Images */}
        <div className="lg:col-span-2">
          <div className="grid gap-4 md:grid-cols-2">
            {generatedImages.map((image) => (
              <Card key={image.id}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(image.status)}
                      <span className="text-sm font-medium">
                        {image.status === 'generating' ? '生成中...' :
                         image.status === 'completed' ? '生成完成' : '生成失敗'}
                      </span>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {image.service}
                    </Badge>
                  </div>
                </CardHeader>
                
                <CardContent className="space-y-3">
                  {image.status === 'generating' && (
                    <div className="aspect-square bg-muted rounded-lg flex items-center justify-center">
                      <div className="text-center">
                        <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
                        <p className="text-sm text-muted-foreground">正在生成圖像...</p>
                      </div>
                    </div>
                  )}
                  
                  {image.status === 'completed' && image.imageData && (
                    <div className="space-y-3">
                      <div className="aspect-square bg-muted rounded-lg overflow-hidden">
                        <img
                          src={`data:image/png;base64,${image.imageData}`}
                          alt={image.prompt}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => downloadImage(image.imageData, `generated-${image.id}.png`)}
                        >
                          <Download className="h-4 w-4 mr-1" />
                          下載
                        </Button>
                        
                        <div className="text-xs text-muted-foreground">
                          {image.size}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {image.status === 'error' && (
                    <div className="aspect-square bg-muted rounded-lg flex items-center justify-center">
                      <div className="text-center">
                        <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
                        <p className="text-sm text-muted-foreground">生成失敗</p>
                      </div>
                    </div>
                  )}
                  
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm text-muted-foreground flex-1">
                        {image.prompt}
                      </p>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0 flex-shrink-0"
                        onClick={() => copyPrompt(image.prompt)}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {formatTime(image.timestamp)}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            
            {generatedImages.length === 0 && (
              <Card className="md:col-span-2">
                <CardContent className="flex items-center justify-center h-64">
                  <div className="text-center">
                    <ImageIcon className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">
                      還沒有生成任何圖像
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                      輸入提示詞並點擊生成按鈕開始創作
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}