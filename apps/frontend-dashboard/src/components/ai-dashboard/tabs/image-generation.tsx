'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui'
import { Button } from '@acme/ui'
import { Input } from '@acme/ui'
import { Textarea } from '@acme/ui'
import { Badge } from '@acme/ui'
import { useToast } from '@/hooks/use-toast'
import { 
  Image as ImageIcon, 
  Download, 
  Sparkles, 
  Loader2,
  Palette,
  Camera,
  Wand2
} from 'lucide-react'

interface GeneratedImage {
  id: string
  prompt: string
  url: string
  timestamp: Date
  size: string
}

export function ImageGeneration() {
  const { toast } = useToast()
  const [prompt, setPrompt] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedImages, setGeneratedImages] = useState<GeneratedImage[]>([
    {
      id: '1',
      prompt: 'A beautiful mountain landscape at sunset',
      url: '/placeholder-image.jpg',
      timestamp: new Date(Date.now() - 3600000),
      size: '1024x1024'
    },
    {
      id: '2',
      prompt: 'Futuristic city with flying cars',
      url: '/placeholder-image.jpg',
      timestamp: new Date(Date.now() - 7200000),
      size: '1024x1024'
    }
  ])

  const imageSizes = [
    { value: '256x256', label: 'Small (256x256)' },
    { value: '512x512', label: 'Medium (512x512)' },
    { value: '1024x1024', label: 'Large (1024x1024)' }
  ]

  const [selectedSize, setSelectedSize] = useState('1024x1024')

  const handleGenerateImage = async () => {
    if (!prompt.trim()) return

    setIsGenerating(true)

    try {
      const response = await fetch('/api/py/image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt,
          size: selectedSize
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to generate image')
      }

      const data = await response.json()
      
      const newImage: GeneratedImage = {
        id: Date.now().toString(),
        prompt,
        url: `data:image/png;base64,${data.image}`,
        timestamp: new Date(),
        size: selectedSize
      }
      setGeneratedImages(prev => [newImage, ...prev])
    } catch (error) {
      console.error('Error generating image:', error)
      toast({
        title: "Error",
        description: "Failed to generate image. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const formatTime = (date: Date) => {
    return date.toLocaleString()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Image Generation</h1>
          <p className="text-muted-foreground">
            Create AI-generated images from text descriptions
          </p>
        </div>
        <Badge variant="outline">
          <ImageIcon className="mr-2 h-4 w-4" />
          {generatedImages.length} images
        </Badge>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Generation Panel */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Generate Image</CardTitle>
              <CardDescription>
                Describe the image you want to create
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Prompt
                </label>
                <Textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="A beautiful landscape with mountains and a lake..."
                  rows={4}
                />
              </div>
              
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Image Size
                </label>
                <div className="grid gap-2">
                  {imageSizes.map((size) => (
                    <Button
                      key={size.value}
                      variant={selectedSize === size.value ? 'default' : 'outline'}
                      size="sm"
                      className="justify-start"
                      onClick={() => setSelectedSize(size.value)}
                    >
                      {size.label}
                    </Button>
                  ))}
                </div>
              </div>

              <Button
                onClick={handleGenerateImage}
                disabled={!prompt.trim() || isGenerating}
                className="w-full"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Wand2 className="mr-2 h-4 w-4" />
                    Generate Image
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          <Card className="mt-4">
            <CardHeader>
              <CardTitle className="text-lg">Tips</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div>• Be descriptive and specific</div>
              <div>• Include style preferences</div>
              <div>• Mention lighting and mood</div>
              <div>• Specify composition if needed</div>
              <div>• Use artistic terms for better results</div>
            </CardContent>
          </Card>
        </div>

        {/* Generated Images */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Generated Images</CardTitle>
              <CardDescription>
                Your AI-generated image gallery
              </CardDescription>
            </CardHeader>
            <CardContent>
              {generatedImages.length === 0 ? (
                <div className="text-center py-12">
                  <ImageIcon className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">No images yet</h3>
                  <p className="text-muted-foreground">
                    Generate your first AI image using the panel on the left
                  </p>
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2">
                  {generatedImages.map((image) => (
                    <Card key={image.id} className="overflow-hidden">
                      <div className="aspect-square bg-muted flex items-center justify-center">
                        {image.url.startsWith('data:image') ? (
                          <img 
                            src={image.url} 
                            alt={image.prompt}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="text-center">
                            <ImageIcon className="mx-auto h-12 w-12 text-muted-foreground mb-2" />
                            <p className="text-sm text-muted-foreground">
                              Generated Image
                            </p>
                          </div>
                        )}
                      </div>
                      <CardContent className="p-4">
                        <div className="space-y-2">
                          <p className="text-sm font-medium line-clamp-2">
                            {image.prompt}
                          </p>
                          <div className="flex items-center justify-between text-xs text-muted-foreground">
                            <span>{image.size}</span>
                            <span>{formatTime(image.timestamp)}</span>
                          </div>
                          <div className="flex gap-2">
                            <Button variant="outline" size="sm" className="flex-1">
                              <Download className="mr-2 h-3 w-3" />
                              Download
                            </Button>
                            <Button variant="outline" size="sm">
                              <Sparkles className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}