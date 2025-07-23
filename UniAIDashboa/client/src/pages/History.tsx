import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  Search,
  Filter,
  Star,
  Trash2,
  Download,
  Copy,
  Calendar,
  Clock,
  MessageSquare,
  Image,
  Mic,
  BarChart3,
  Code,
  Volume2
} from 'lucide-react'
import { getHistory, toggleHistoryFavorite, deleteHistoryItem } from '@/api/history'
import { useToast } from '@/hooks/useToast'
import { motion } from 'framer-motion'
import { format } from 'date-fns'

const iconMap = {
  'gpt-4': MessageSquare,
  'claude': MessageSquare,
  'dalle-3': Image,
  'stable-diffusion': Image,
  'whisper': Mic,
  'tts': Volume2,
  'code-generation': Code,
  'data-processing': BarChart3,
}

export function History() {
  const [history, setHistory] = useState<any[]>([])
  const [filteredHistory, setFilteredHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [serviceFilter, setServiceFilter] = useState('all')
  const [favoriteFilter, setFavoriteFilter] = useState('all')
  const { toast } = useToast()

  useEffect(() => {
    loadHistory()
  }, [])

  useEffect(() => {
    filterHistory()
  }, [history, searchTerm, serviceFilter, favoriteFilter])

  const loadHistory = async () => {
    try {
      console.log('Loading history...')
      const response = await getHistory()
      setHistory((response as any).history)
      console.log('History loaded successfully')
    } catch (error) {
      console.error('Error loading history:', error)
      toast({
        title: "Error",
        description: "Failed to load history",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const filterHistory = () => {
    let filtered = history

    if (searchTerm) {
      filtered = filtered.filter(item =>
        item.input.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.output.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.serviceName.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    if (serviceFilter !== 'all') {
      filtered = filtered.filter(item => item.serviceId === serviceFilter)
    }

    if (favoriteFilter === 'favorites') {
      filtered = filtered.filter(item => item.favorite)
    }

    setFilteredHistory(filtered)
  }

  const handleToggleFavorite = async (id: string, favorite: boolean) => {
    try {
      await toggleHistoryFavorite(id, !favorite)
      setHistory(prev => prev.map(item =>
        item._id === id ? { ...item, favorite: !favorite } : item
      ))
      toast({
        title: "Success",
        description: favorite ? "Removed from favorites" : "Added to favorites",
      })
    } catch (error) {
      console.error('Error toggling favorite:', error)
      toast({
        title: "Error",
        description: "Failed to update favorite status",
        variant: "destructive",
      })
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteHistoryItem(id)
      setHistory(prev => prev.filter(item => item._id !== id))
      toast({
        title: "Success",
        description: "Item deleted successfully",
      })
    } catch (error) {
      console.error('Error deleting item:', error)
      toast({
        title: "Error",
        description: "Failed to delete item",
        variant: "destructive",
      })
    }
  }

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text)
    toast({
      title: "Copied",
      description: "Content copied to clipboard",
    })
  }

  const services = Array.from(new Set(history.map(item => item.serviceId)))

  if (loading) {
    return (
      <div className="space-y-6">
        {[...Array(3)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader className="space-y-2">
              <div className="h-4 bg-muted rounded w-3/4"></div>
              <div className="h-3 bg-muted rounded w-1/2"></div>
            </CardHeader>
            <CardContent>
              <div className="h-20 bg-muted rounded"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            History
          </h1>
          <p className="text-muted-foreground mt-1">View and manage your AI interaction history</p>
        </div>
        <Badge variant="secondary" className="text-sm">
          {filteredHistory.length} items
        </Badge>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search history..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={serviceFilter} onValueChange={setServiceFilter}>
          <SelectTrigger className="w-full sm:w-[200px]">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Filter by service" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Services</SelectItem>
            {services.map((service) => (
              <SelectItem key={service} value={service}>
                {service.toUpperCase()}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={favoriteFilter} onValueChange={setFavoriteFilter}>
          <SelectTrigger className="w-full sm:w-[150px]">
            <Star className="h-4 w-4 mr-2" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Items</SelectItem>
            <SelectItem value="favorites">Favorites Only</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* History Items */}
      <div className="space-y-4">
        {filteredHistory.map((item, index) => {
          const IconComponent = iconMap[item.serviceId as keyof typeof iconMap] || MessageSquare
          return (
            <motion.div
              key={item._id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="bg-card/50 backdrop-blur-sm hover:shadow-lg transition-all duration-300">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-gradient-to-r from-blue-500/20 to-purple-500/20">
                        <IconComponent className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{item.serviceName}</CardTitle>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {format(new Date(item.timestamp), 'MMM dd, yyyy')}
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {item.processingTime}s
                          </div>
                          {item.tokensUsed && (
                            <div>{item.tokensUsed} tokens</div>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleToggleFavorite(item._id, item.favorite)}
                        className={item.favorite ? 'text-yellow-500' : ''}
                      >
                        <Star className={`h-4 w-4 ${item.favorite ? 'fill-current' : ''}`} />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCopy(item.output)}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(item._id)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label className="text-sm font-medium text-muted-foreground">Input:</Label>
                    <div className="mt-1 p-3 bg-muted/50 rounded-lg text-sm">
                      {item.input.length > 200 ? `${item.input.substring(0, 200)}...` : item.input}
                    </div>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-muted-foreground">Output:</Label>
                    <div className="mt-1 p-3 bg-background/50 rounded-lg text-sm border">
                      {item.serviceId === 'dalle-3' || item.serviceId === 'stable-diffusion' ? (
                        <img
                          src={item.output}
                          alt="Generated content"
                          className="max-w-xs rounded-lg"
                        />
                      ) : (
                        <div>
                          {item.output.length > 300 ? `${item.output.substring(0, 300)}...` : item.output}
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )
        })}
      </div>

      {filteredHistory.length === 0 && (
        <div className="text-center py-12">
          <div className="text-muted-foreground">No history items found matching your criteria.</div>
        </div>
      )}
    </div>
  )
}