import { useState, useEffect } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Play,
  Square,
  Download,
  Copy,
  Share,
  Star,
  Settings,
  Upload,
  FileText,
  Image as ImageIcon,
  Mic,
  Code,
  Loader2
} from 'lucide-react'
import { getAIServices, executeAIService } from '@/api/aiServices'
import { useToast } from '@/hooks/useToast'
import { motion } from 'framer-motion'
import { useDropzone } from 'react-dropzone'

export function ServiceInterface() {
  const { serviceId } = useParams()
  const [searchParams] = useSearchParams()
  const mode = searchParams.get('mode') || 'quick'
  
  const [service, setService] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [input, setInput] = useState('')
  const [result, setResult] = useState<any>(null)
  const [parameters, setParameters] = useState<any>({})
  const [files, setFiles] = useState<File[]>([])
  
  const { toast } = useToast()

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => {
      setFiles(acceptedFiles)
      console.log('Files uploaded:', acceptedFiles)
    },
    multiple: false,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif'],
      'audio/*': ['.mp3', '.wav', '.m4a'],
      'text/*': ['.txt', '.md'],
    }
  })

  useEffect(() => {
    loadService()
  }, [serviceId])

  const loadService = async () => {
    try {
      console.log('Loading service:', serviceId)
      const response = await getAIServices()
      const foundService = (response as any).services.find((s: any) => s.id === serviceId)
      
      if (foundService) {
        setService(foundService)
        initializeParameters(foundService)
      }
      console.log('Service loaded:', foundService)
    } catch (error) {
      console.error('Error loading service:', error)
      toast({
        title: "Error",
        description: "Failed to load service details",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const initializeParameters = (service: any) => {
    const defaultParams: any = {}
    
    switch (service.id) {
      case 'gpt-4':
      case 'claude':
        defaultParams.temperature = 0.7
        defaultParams.maxTokens = 1000
        defaultParams.topP = 1
        break
      case 'dalle-3':
      case 'stable-diffusion':
        defaultParams.size = '1024x1024'
        defaultParams.quality = 'standard'
        defaultParams.style = 'natural'
        break
      case 'whisper':
        defaultParams.language = 'auto'
        defaultParams.format = 'text'
        break
      case 'tts':
        defaultParams.voice = 'alloy'
        defaultParams.speed = 1.0
        break
    }
    
    setParameters(defaultParams)
  }

  const handleExecute = async () => {
    if (!input && files.length === 0) {
      toast({
        title: "Error",
        description: "Please provide input text or upload a file",
        variant: "destructive",
      })
      return
    }

    setProcessing(true)
    setProgress(0)
    setResult(null)

    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval)
          return prev
        }
        return prev + Math.random() * 10
      })
    }, 200)

    try {
      console.log('Executing service:', serviceId, { input, parameters, files })
      
      const inputData = files.length > 0 ? files[0].name : input
      const response = await executeAIService({
        serviceId: serviceId!,
        parameters,
        input: inputData
      })

      setResult(response)
      setProgress(100)
      console.log('Service execution completed:', response)
      
      toast({
        title: "Success",
        description: "Service executed successfully",
      })
    } catch (error) {
      console.error('Error executing service:', error)
      toast({
        title: "Error",
        description: "Failed to execute service",
        variant: "destructive",
      })
    } finally {
      clearInterval(progressInterval)
      setProcessing(false)
      setTimeout(() => setProgress(0), 2000)
    }
  }

  const handleCopy = () => {
    if (result?.result) {
      navigator.clipboard.writeText(result.result)
      toast({
        title: "Copied",
        description: "Result copied to clipboard",
      })
    }
  }

  const handleDownload = () => {
    if (result?.result) {
      const blob = new Blob([result.result], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${service?.name}-result.txt`
      a.click()
      URL.revokeObjectURL(url)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  if (!service) {
    return (
      <div className="text-center py-12">
        <div className="text-muted-foreground">Service not found</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Service Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            {service.name}
          </h1>
          <p className="text-muted-foreground mt-1">{service.description}</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary">{service.category}</Badge>
          <Badge className={service.status === 'active' ? 'bg-green-500' : 'bg-yellow-500'}>
            {service.status}
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Section */}
        <Card className="bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Input & Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <Tabs defaultValue="text" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="text">Text Input</TabsTrigger>
                <TabsTrigger value="file">File Upload</TabsTrigger>
              </TabsList>
              
              <TabsContent value="text" className="space-y-4">
                <div>
                  <Label htmlFor="input">Input Text</Label>
                  <Textarea
                    id="input"
                    placeholder={`Enter your ${service.category.toLowerCase()} input here...`}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    rows={6}
                    className="mt-2"
                  />
                </div>
              </TabsContent>
              
              <TabsContent value="file" className="space-y-4">
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                    isDragActive ? 'border-blue-500 bg-blue-50 dark:bg-blue-950' : 'border-muted-foreground/25'
                  }`}
                >
                  <input {...getInputProps()} />
                  <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                  {isDragActive ? (
                    <p>Drop the file here...</p>
                  ) : (
                    <div>
                      <p>Drag & drop a file here, or click to select</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        Supports images, audio, and text files
                      </p>
                    </div>
                  )}
                </div>
                
                {files.length > 0 && (
                  <div className="space-y-2">
                    {files.map((file, index) => (
                      <div key={index} className="flex items-center gap-2 p-2 bg-muted rounded">
                        <FileText className="h-4 w-4" />
                        <span className="text-sm">{file.name}</span>
                        <span className="text-xs text-muted-foreground">
                          ({(file.size / 1024).toFixed(1)} KB)
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </TabsContent>
            </Tabs>

            {mode === 'advanced' && (
              <div className="space-y-4 pt-4 border-t">
                <h4 className="font-medium">Advanced Parameters</h4>
                
                {service.id === 'gpt-4' || service.id === 'claude' ? (
                  <>
                    <div>
                      <Label>Temperature: {parameters.temperature}</Label>
                      <Slider
                        value={[parameters.temperature]}
                        onValueChange={(value) => setParameters({...parameters, temperature: value[0]})}
                        max={2}
                        min={0}
                        step={0.1}
                        className="mt-2"
                      />
                    </div>
                    <div>
                      <Label>Max Tokens</Label>
                      <Input
                        type="number"
                        value={parameters.maxTokens}
                        onChange={(e) => setParameters({...parameters, maxTokens: parseInt(e.target.value)})}
                        className="mt-2"
                      />
                    </div>
                  </>
                ) : service.id === 'dalle-3' || service.id === 'stable-diffusion' ? (
                  <>
                    <div>
                      <Label>Image Size</Label>
                      <Select
                        value={parameters.size}
                        onValueChange={(value) => setParameters({...parameters, size: value})}
                      >
                        <SelectTrigger className="mt-2">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="512x512">512x512</SelectItem>
                          <SelectItem value="1024x1024">1024x1024</SelectItem>
                          <SelectItem value="1792x1024">1792x1024</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Quality</Label>
                      <Select
                        value={parameters.quality}
                        onValueChange={(value) => setParameters({...parameters, quality: value})}
                      >
                        <SelectTrigger className="mt-2">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="standard">Standard</SelectItem>
                          <SelectItem value="hd">HD</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </>
                ) : null}
              </div>
            )}

            <div className="flex gap-2 pt-4">
              <Button
                onClick={handleExecute}
                disabled={processing}
                className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
              >
                {processing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Execute
                  </>
                )}
              </Button>
              {processing && (
                <Button variant="outline" onClick={() => setProcessing(false)}>
                  <Square className="h-4 w-4" />
                </Button>
              )}
            </div>

            {processing && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Processing...</span>
                  <span>{Math.round(progress)}%</span>
                </div>
                <Progress value={progress} className="w-full" />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results Section */}
        <Card className="bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            {result ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    Processing time: {result.processingTime}s
                    {result.tokensUsed && ` • Tokens: ${result.tokensUsed}`}
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={handleCopy}>
                      <Copy className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="sm" onClick={handleDownload}>
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <Share className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <Star className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div className="border rounded-lg p-4 bg-background/50">
                  {service.id === 'dalle-3' || service.id === 'stable-diffusion' ? (
                    <img
                      src={result.result}
                      alt="Generated image"
                      className="w-full rounded-lg"
                    />
                  ) : (
                    <pre className="whitespace-pre-wrap text-sm">{result.result}</pre>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Results will appear here after execution</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}