'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui'
import { Button } from '@acme/ui'
import { Input } from '@acme/ui'
import { Textarea } from '@acme/ui'
import { Badge } from '@acme/ui'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@acme/ui'
import { useToast } from '@/hooks/use-toast'
import { useImageHistory, useImageStatistics } from '@/hooks/use-api-data'
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
  HardDrive
} from 'lucide-react'

export function ImageGeneration() {
  const { toast } = useToast()
  const [prompt, setPrompt] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [selectedImages, setSelectedImages] = useState<string[]>([])
  
  // API hooks
  const { data: imageHistory, loading: historyLoading, error: historyError, refresh: refreshHistory, deleteImage, batchDeleteImages } = useImageHistory()
  const { data: statistics, loading: statsLoading, refresh: refreshStats } = useImageStatistics()
  
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
      
      <Tabs defaultValue="generate" className="space-y-4">
        <TabsList>
          <TabsTrigger value="generate">Generate</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
          <TabsTrigger value="statistics">Statistics</TabsTrigger>
        </TabsList>
        
        <TabsContent value="generate" className="space-y-4">

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

            {/* Recent Images Preview */}
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle>Recent Images</CardTitle>
                  <CardDescription>
                    Latest generated images (view all in History tab)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {currentImages.length === 0 ? (
                    <div className="text-center py-12">
                      <ImageIcon className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                      <h3 className="text-lg font-medium mb-2">No images yet</h3>
                      <p className="text-muted-foreground">
                        Generate your first AI image using the panel on the left
                      </p>
                    </div>
                  ) : (
                    <div className="grid gap-4 md:grid-cols-2">
                      {currentImages.slice(0, 4).map((image) => (
                        <Card key={image.id} className="overflow-hidden">
                          <div className="aspect-square bg-muted flex items-center justify-center">
                            <div className="text-center">
                              <ImageIcon className="mx-auto h-12 w-12 text-muted-foreground mb-2" />
                              <p className="text-sm text-muted-foreground">
                                Generated Image
                              </p>
                            </div>
                          </div>
                          <CardContent className="p-4">
                            <div className="space-y-2">
                              <p className="text-sm font-medium line-clamp-2">
                                {image.prompt}
                              </p>
                              <div className="flex items-center justify-between text-xs text-muted-foreground">
                                <span>{image.size}</span>
                                <span>{formatTime(image.created_at)}</span>
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
        </TabsContent>
        
        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Image History</CardTitle>
                  <CardDescription>
                    Manage your generated images
                  </CardDescription>
                </div>
                {selectedImages.length > 0 && (
                  <Button 
                    variant="destructive" 
                    size="sm" 
                    onClick={handleBatchDelete}
                    disabled={batchDeleteLoading}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete Selected ({selectedImages.length})
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {historyLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin" />
                  <span className="ml-2">Loading images...</span>
                </div>
              ) : historyError ? (
                <div className="text-center py-8">
                  <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Failed to load images</h3>
                  <p className="text-muted-foreground mb-4">{historyError}</p>
                  <Button onClick={refreshHistory}>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Retry
                  </Button>
                </div>
              ) : currentImages.length === 0 ? (
                <div className="text-center py-12">
                  <ImageIcon className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">No images found</h3>
                  <p className="text-muted-foreground">
                    Generate some images to see them here
                  </p>
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {currentImages.map((image) => (
                    <Card key={image.id} className="overflow-hidden">
                      <div className="relative">
                        <div className="aspect-square bg-muted flex items-center justify-center">
                          <div className="text-center">
                            <ImageIcon className="mx-auto h-12 w-12 text-muted-foreground mb-2" />
                            <p className="text-sm text-muted-foreground">
                              Generated Image
                            </p>
                          </div>
                        </div>
                        <div className="absolute top-2 left-2">
                          <input
                            type="checkbox"
                            checked={selectedImages.includes(image.id)}
                            onChange={() => toggleImageSelection(image.id)}
                            className="w-4 h-4"
                          />
                        </div>
                      </div>
                      <CardContent className="p-4">
                        <div className="space-y-2">
                          <p className="text-sm font-medium line-clamp-2">
                            {image.prompt}
                          </p>
                          <div className="flex items-center justify-between text-xs text-muted-foreground">
                            <span>{image.size}</span>
                            <span>{formatBytes(image.file_size)}</span>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {formatTime(image.created_at)}
                          </div>
                          <div className="flex gap-2">
                            <Button variant="outline" size="sm" className="flex-1">
                              <Download className="mr-2 h-3 w-3" />
                              Download
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => handleDeleteImage(image.id)}
                              disabled={deleteLoading}
                            >
                              <Trash2 className="h-3 w-3" />
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
        </TabsContent>
        
        <TabsContent value="statistics" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Images</CardTitle>
                <ImageIcon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{currentStats.total_images}</div>
                <p className="text-xs text-muted-foreground">
                  All time generated
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Storage Used</CardTitle>
                <HardDrive className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatBytes(currentStats.total_size)}</div>
                <p className="text-xs text-muted-foreground">
                  Total file size
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">This Month</CardTitle>
                <Calendar className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{currentStats.images_this_month}</div>
                <p className="text-xs text-muted-foreground">
                  +{currentStats.images_this_week} this week
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg. Generation</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{currentStats.average_generation_time}s</div>
                <p className="text-xs text-muted-foreground">
                  Average time
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}