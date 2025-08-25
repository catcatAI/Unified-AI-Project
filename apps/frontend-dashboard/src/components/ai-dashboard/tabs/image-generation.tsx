'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui'
import { Button } from '@acme/ui'
import { Input } from '@acme/ui'
import { Textarea } from '@acme/ui'
import { Badge } from '@acme/ui'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@acme/ui'
import { useToast } from '@/hooks/use-toast'
import { useImageHistory, useImageStatistics, useImageArchive } from '@/hooks/use-api-data'
import { 
  Image as ImageIcon, 
  Download, 
  Sparkles, 
  Loader2,
  Palette,
  Camera,
  Wand2,
  Trash2,
  RefreshCw,
  AlertTriangle,
  BarChart3,
  Calendar,
  HardDrive,
  Archive
} from 'lucide-react'

export function ImageGeneration() {
  const { toast } = useToast()
  const [prompt, setPrompt] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [selectedImages, setSelectedImages] = useState<string[]>([])
  
  // API hooks
  const { data: imageHistory, loading: historyLoading, error: historyError, refresh: refreshHistory, deleteImage, batchDeleteImages } = useImageHistory()
  const { data: statistics, loading: statsLoading, refresh: refreshStats } = useImageStatistics()
  const { saveImageToArchive } = useImageArchive()
  
  // Mock data for fallback
  const mockImages = [
    {
      id: '1',
      prompt: 'A beautiful mountain landscape at sunset',
      url: '/placeholder-image.jpg',
      created_at: new Date(Date.now() - 3600000).toISOString(),
      size: '1024x1024',
      file_size: 2048576
    },
    {
      id: '2',
      prompt: 'Futuristic city with flying cars',
      url: '/placeholder-image.jpg',
      created_at: new Date(Date.now() - 7200000).toISOString(),
      size: '1024x1024',
      file_size: 1856432
    }
  ]

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
      const response = await fetch('/api/v1/image', {
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
      
      // Save to archive
      await saveImageToArchive(prompt, data.url, { size: selectedSize })
      
      toast({
        title: "Success",
        description: "Image generated successfully!",
      })
      
      // Refresh the image history to show the new image
      refreshHistory()
      refreshStats()
      setPrompt('') // Clear the prompt
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
  
  const handleDeleteImage = async (imageId: string) => {
    try {
      await deleteImage(imageId)
      toast({
        title: "Success",
        description: "Image deleted successfully!",
      })
      refreshHistory()
      refreshStats()
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete image.",
        variant: "destructive",
      })
    }
  }
  
  const handleBatchDelete = async () => {
    if (selectedImages.length === 0) return
    
    try {
      await batchDeleteImages(selectedImages)
      toast({
        title: "Success",
        description: `${selectedImages.length} images deleted successfully!`,
      })
      setSelectedImages([])
      refreshHistory()
      refreshStats()
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete images.",
        variant: "destructive",
      })
    }
  }
  
  const toggleImageSelection = (imageId: string) => {
    setSelectedImages(prev => 
      prev.includes(imageId) 
        ? prev.filter(id => id !== imageId)
        : [...prev, imageId]
    )
  }
  
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }
  
  // Use real data when available, fallback to mock data
  const currentImages = imageHistory || mockImages
  const currentStats = statistics || {
    total_images: mockImages.length,
    total_size: mockImages.reduce((sum, img) => sum + img.file_size, 0),
    images_today: 1,
    images_this_week: 2,
    images_this_month: 2,
    average_generation_time: 3.2
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
        <div className="flex gap-2">
          <Badge variant="outline">
            <ImageIcon className="mr-2 h-4 w-4" />
            {currentStats.total_images} images
          </Badge>
          <Badge variant="outline">
            <HardDrive className="mr-2 h-4 w-4" />
            {formatBytes(currentStats.total_size)}
          </Badge>
          <Button variant="outline" size="sm" onClick={() => { refreshHistory(); refreshStats(); }} disabled={historyLoading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${historyLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Generation Panel */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                Create New Image
              </CardTitle>
              <CardDescription>
                Generate images from text prompts
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Prompt</label>
                <Textarea
                  placeholder="Describe the image you want to generate..."
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  rows={4}
                />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">Size</label>
                <div className="grid grid-cols-3 gap-2">
                  {imageSizes.map((size) => (
                    <Button
                      key={size.value}
                      variant={selectedSize === size.value ? "default" : "outline"}
                      size="sm"
                      onClick={() => setSelectedSize(size.value)}
                    >
                      {size.label}
                    </Button>
                  ))}
                </div>
              </div>
              
              <Button
                className="w-full"
                onClick={handleGenerateImage}
                disabled={isGenerating || !prompt.trim()}
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
          
          {/* Statistics */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Statistics
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-2xl font-bold">{currentStats.total_images}</div>
                  <div className="text-sm text-muted-foreground">Total Images</div>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-2xl font-bold">{currentStats.images_today}</div>
                  <div className="text-sm text-muted-foreground">Today</div>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-2xl font-bold">{currentStats.images_this_week}</div>
                  <div className="text-sm text-muted-foreground">This Week</div>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-2xl font-bold">{currentStats.images_this_month}</div>
                  <div className="text-sm text-muted-foreground">This Month</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Image Gallery */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ImageIcon className="h-5 w-5" />
                Generated Images
              </CardTitle>
              <CardDescription>
                Your image generation history
              </CardDescription>
            </CardHeader>
            <CardContent>
              {historyLoading ? (
                <div className="flex items-center justify-center p-8">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              ) : historyError ? (
                <div className="flex flex-col items-center justify-center p-8 text-center">
                  <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
                  <h3 className="text-lg font-medium mb-2">Error Loading Images</h3>
                  <p className="text-muted-foreground mb-4">{historyError}</p>
                  <Button onClick={refreshHistory}>Retry</Button>
                </div>
              ) : currentImages.length === 0 ? (
                <div className="flex flex-col items-center justify-center p-8 text-center">
                  <ImageIcon className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">No Images Generated</h3>
                  <p className="text-muted-foreground">
                    Start by creating your first AI-generated image using the panel on the left.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {currentImages.map((image) => (
                    <div 
                      key={image.id} 
                      className={`border rounded-lg overflow-hidden group relative ${
                        selectedImages.includes(image.id) ? 'ring-2 ring-primary' : ''
                      }`}
                    >
                      <div 
                        className="aspect-square bg-muted relative cursor-pointer"
                        onClick={() => toggleImageSelection(image.id)}
                      >
                        <img 
                          src={image.url} 
                          alt={image.prompt}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                          <Button 
                            size="sm" 
                            variant="secondary"
                            onClick={(e) => {
                              e.stopPropagation();
                              // Download image
                              const link = document.createElement('a');
                              link.href = image.url;
                              link.download = `generated-image-${image.id}.png`;
                              link.click();
                            }}
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                          <Button 
                            size="sm" 
                            variant="secondary"
                            onClick={(e) => {
                              e.stopPropagation();
                              // Save to archive
                              saveImageToArchive(image.prompt, image.url, { size: image.size });
                              toast({
                                title: "Saved",
                                description: "Image saved to archive",
                              });
                            }}
                          >
                            <Archive className="h-4 w-4" />
                          </Button>
                          <Button 
                            size="sm" 
                            variant="destructive"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteImage(image.id);
                            }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                      <div className="p-3">
                        <p className="text-sm font-medium truncate" title={image.prompt}>
                          {image.prompt}
                        </p>
                        <div className="flex items-center justify-between mt-2">
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Calendar className="h-3 w-3" />
                            {formatTime(image.created_at)}
                          </div>
                          <Badge variant="secondary" className="text-xs">
                            {image.size}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {selectedImages.length > 0 && (
                <div className="mt-4 flex justify-end">
                  <Button
                    variant="destructive"
                    onClick={handleBatchDelete}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete Selected ({selectedImages.length})
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}