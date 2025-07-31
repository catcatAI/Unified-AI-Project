'use client'

import { useState, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Image as ImageIcon, 
  Download, 
  Loader2,
  Sparkles,
  Copy,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Palette,
  Wand2,
  Settings,
  History,
  Share,
  Heart,
  Zap,
  Camera,
  Layers
} from 'lucide-react'

interface GeneratedImage {
  id: string
  prompt: string
  imageData: string
  size: string
  service: string
  timestamp: Date
  status: 'generating' | 'completed' | 'error'
  style?: string
  quality?: string
  likes?: number
}

const sizeOptions = [
  { value: '256x256', label: '256×256 (小)', description: '快速生成，適合圖標' },
  { value: '512x512', label: '512×512 (中)', description: '平衡質量和速度' },
  { value: '1024x1024', label: '1024×1024 (大)', description: '高質量，適合打印' },
  { value: '1024x1792', label: '1024×1792 (豎向)', description: '手機壁紙尺寸' },
  { value: '1792x1024', label: '1792×1024 (橫向)', description: '桌面壁紙尺寸' }
]

const styleOptions = [
  { value: 'realistic', label: '寫實風格', icon: Camera },
  { value: 'artistic', label: '藝術風格', icon: Palette },
  { value: 'cartoon', label: '卡通風格', icon: Layers },
  { value: 'abstract', label: '抽象風格', icon: Sparkles },
  { value: 'vintage', label: '復古風格', icon: History }
]

const qualityOptions = [
  { value: 'standard', label: '標準質量', description: '快速生成' },
  { value: 'hd', label: '高質量', description: '更好細節' },
  { value: 'ultra', label: '超高質量', description: '最佳細節' }
]

const promptExamples = [
  { 
    title: '可愛動物', 
    prompt: '一個可愛的貓咪在花園中玩耍，陽光灑在毛茸茸的身體上，背景是盛開的花朵',
    category: 'animals'
  },
  { 
    title: '未來城市', 
    prompt: '未來主義的城市景觀，霓虹燈閃爍，飛行汽車在高樓大廈間穿梭，充滿科技感',
    category: 'scifi'
  },
  { 
    title: '自然風景', 
    prompt: '美麗的山水畫，有山有水有雲，晨霧繚繞，陽光穿透雲層灑在湖面上',
    category: 'nature'
  },
  { 
    title: '抽象藝術', 
    prompt: '抽象藝術，色彩繽紛的幾何圖形，流動的線條，充滿動感和現代感',
    category: 'abstract'
  },
  { 
    title: '溫馨場景', 
    prompt: '溫馨的咖啡館內景，有書籍和咖啡，暖色調燈光，舒適的氛圍',
    category: 'interior'
  },
  { 
    title: '奇幻世界', 
    prompt: '奇幻的魔法森林，發光的植物，飄浮的島嶼，神秘的生物，夢幻般的色彩',
    category: 'fantasy'
  }
]

export function UnifiedImageGeneration() {
  const [prompt, setPrompt] = useState('')
  const [selectedSize, setSelectedSize] = useState('1024x1024')
  const [selectedStyle, setSelectedStyle] = useState('realistic')
  const [selectedQuality, setSelectedQuality] = useState('hd')
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedImages, setGeneratedImages] = useState<GeneratedImage[]>([])
  const [selectedCategory, setSelectedCategory] = useState('all')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const categories = [
    { id: 'all', name: '全部', count: promptExamples.length },
    { id: 'animals', name: '動物', count: promptExamples.filter(p => p.category === 'animals').length },
    { id: 'scifi', name: '科幻', count: promptExamples.filter(p => p.category === 'scifi').length },
    { id: 'nature', name: '自然', count: promptExamples.filter(p => p.category === 'nature').length },
    { id: 'abstract', name: '抽象', count: promptExamples.filter(p => p.category === 'abstract').length },
    { id: 'interior', name: '室內', count: promptExamples.filter(p => p.category === 'interior').length },
    { id: 'fantasy', name: '奇幻', count: promptExamples.filter(p => p.category === 'fantasy').length }
  ]

  const filteredExamples = selectedCategory === 'all' 
    ? promptExamples 
    : promptExamples.filter(p => p.category === selectedCategory)

  const handleGenerateImage = async () => {
    if (!prompt.trim() || isGenerating) return

    const newImage: GeneratedImage = {
      id: Date.now().toString(),
      prompt,
      imageData: '',
      size: selectedSize,
      service: 'unified-ai',
      timestamp: new Date(),
      status: 'generating',
      style: selectedStyle,
      quality: selectedQuality,
      likes: 0
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

  const handleLikeImage = (imageId: string) => {
    setGeneratedImages(prev => prev.map(img => 
      img.id === imageId 
        ? { ...img, likes: (img.likes || 0) + 1 }
        : img
    ))
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
        
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="flex items-center gap-1">
            <Palette className="h-3 w-3" />
            {styleOptions.find(s => s.value === selectedStyle)?.label}
          </Badge>
          <Button variant="outline" onClick={clearHistory} disabled={generatedImages.length === 0}>
            <RefreshCw className="h-4 w-4 mr-1" />
            清除歷史
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Generation Panel */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wand2 className="h-5 w-5" />
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
                  placeholder="詳細描述您想要生成的圖像，包括風格、顏色、構圖等..."
                  className="min-h-[120px]"
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
                        <div>
                          <div>{option.label}</div>
                          <div className="text-xs text-muted-foreground">{option.description}</div>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">藝術風格</label>
                <div className="grid grid-cols-3 gap-2">
                  {styleOptions.map((style) => (
                    <Button
                      key={style.value}
                      variant={selectedStyle === style.value ? "default" : "outline"}
                      size="sm"
                      onClick={() => setSelectedStyle(style.value)}
                      disabled={isGenerating}
                      className="text-xs p-2 h-auto flex flex-col items-center gap-1"
                    >
                      <style.icon className="h-4 w-4" />
                      {style.label}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">圖像質量</label>
                <Select value={selectedQuality} onValueChange={setSelectedQuality} disabled={isGenerating}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {qualityOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        <div>
                          <div>{option.label}</div>
                          <div className="text-xs text-muted-foreground">{option.description}</div>
                        </div>
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
                    <Sparkles className="h-4 w-4 mr-2" />
                    生成圖像
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Zap className="h-4 w-4" />
                快速示例
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
                <TabsList className="grid w-full grid-cols-4 h-auto">
                  {categories.slice(0, 4).map(category => (
                    <TabsTrigger key={category.id} value={category.id} className="text-xs p-1">
                      {category.name}
                    </TabsTrigger>
                  ))}
                </TabsList>
                
                <TabsContent value={selectedCategory} className="space-y-2">
                  {filteredExamples.slice(0, 3).map((example, index) => (
                    <div
                      key={index}
                      className="p-3 rounded-lg border cursor-pointer hover:border-primary/50 transition-colors hover:shadow-sm"
                      onClick={() => applyExamplePrompt(example.prompt)}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="text-sm font-medium">{example.title}</div>
                        <Badge variant="outline" className="text-xs">
                          {categories.find(c => c.id === example.category)?.name}
                        </Badge>
                      </div>
                      <div className="text-xs text-muted-foreground line-clamp-2">
                        {example.prompt}
                      </div>
                    </div>
                  ))}
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>

        {/* Generated Images */}
        <div className="lg:col-span-3">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {generatedImages.map((image) => (
              <Card key={image.id} className="hover:shadow-lg transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(image.status)}
                      <span className="text-sm font-medium">
                        {image.status === 'generating' ? '生成中...' :
                         image.status === 'completed' ? '生成完成' : '生成失敗'}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Badge variant="outline" className="text-xs">
                        {image.service}
                      </Badge>
                      {image.style && (
                        <Badge variant="secondary" className="text-xs">
                          {image.style}
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardHeader>
                
                <CardContent className="space-y-3">
                  {image.status === 'generating' && (
                    <div className="aspect-square bg-muted rounded-lg flex items-center justify-center">
                      <div className="text-center">
                        <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
                        <p className="text-sm text-muted-foreground">正在生成圖像...</p>
                        <p className="text-xs text-muted-foreground mt-1">預計需要10-30秒</p>
                      </div>
                    </div>
                  )}
                  
                  {image.status === 'completed' && image.imageData && (
                    <div className="space-y-3">
                      <div className="aspect-square bg-muted rounded-lg overflow-hidden group">
                        <img
                          src={`data:image/png;base64,${image.imageData}`}
                          alt={image.prompt}
                          className="w-full h-full object-cover transition-transform group-hover:scale-105"
                        />
                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                          <div className="flex gap-2">
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => downloadImage(image.imageData, `generated-${image.id}.png`)}
                            >
                              <Download className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => handleLikeImage(image.id)}
                            >
                              <Heart className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => downloadImage(image.imageData, `generated-${image.id}.png`)}
                          >
                            <Download className="h-4 w-4 mr-1" />
                            下載
                          </Button>
                          {image.likes !== undefined && (
                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                              <Heart className="h-3 w-3 text-red-500" />
                              {image.likes}
                            </div>
                          )}
                        </div>
                        
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
                        <p className="text-xs text-muted-foreground mt-1">請稍後重試</p>
                      </div>
                    </div>
                  )}
                  
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm text-muted-foreground flex-1 line-clamp-2">
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
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>{formatTime(image.timestamp)}</span>
                      {image.quality && (
                        <Badge variant="outline" className="text-xs">
                          {image.quality}
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            
            {generatedImages.length === 0 && (
              <Card className="md:col-span-2 xl:col-span-3">
                <CardContent className="flex items-center justify-center h-96">
                  <div className="text-center max-w-md">
                    <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                      <ImageIcon className="h-8 w-8 text-primary" />
                    </div>
                    <h3 className="text-lg font-medium mb-2">開始創作您的第一張圖像</h3>
                    <p className="text-muted-foreground mb-4">
                      輸入詳細的描述提示詞，選擇風格和尺寸，然後點擊生成按鈕
                    </p>
                    <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                      <Sparkles className="h-4 w-4" />
                      <span>AI 將為您生成獨一無二的圖像作品</span>
                    </div>
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