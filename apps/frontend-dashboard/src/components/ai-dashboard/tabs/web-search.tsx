'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/hooks/use-toast'
import { 
  Search, 
  Globe, 
  Clock, 
  ExternalLink,
  Loader2,
  TrendingUp,
  Star,
  Copy
} from 'lucide-react'

interface SearchResult {
  id: string
  title: string
  url: string
  snippet: string
  hostName: string
  timestamp: Date
  rank: number
}

export function WebSearch() {
  const { toast } = useToast()
  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [searchResults, setSearchResults] = useState<SearchResult[]>([
    {
      id: '1',
      title: 'Latest AI Developments in 2024',
      url: 'https://example.com/ai-developments-2024',
      snippet: 'Artificial intelligence continues to evolve rapidly with breakthroughs in natural language processing, computer vision, and machine learning...',
      hostName: 'techcrunch.com',
      timestamp: new Date(Date.now() - 1800000),
      rank: 1
    },
    {
      id: '2',
      title: 'Understanding Neural Networks: A Complete Guide',
      url: 'https://example.com/neural-networks-guide',
      snippet: 'Neural networks are computing systems inspired by biological neural networks. Learn about their architecture, training methods, and applications...',
      hostName: 'example.com',
      timestamp: new Date(Date.now() - 1800000),
      rank: 2
    },
    {
      id: '3',
      title: 'The Future of Machine Learning',
      url: 'https://example.com/future-ml',
      snippet: 'Machine learning is transforming industries across the globe. From healthcare to finance, ML algorithms are revolutionizing how we process data...',
      hostName: 'ai-news.com',
      timestamp: new Date(Date.now() - 1800000),
      rank: 3
    }
  ])

  const trendingSearches = [
    'Artificial Intelligence trends 2024',
    'Machine learning algorithms',
    'Neural network architectures',
    'AI in healthcare',
    'Natural language processing'
  ]

  const handleSearch = async () => {
    if (!query.trim()) return

    setIsSearching(true)

    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          num: 10
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to perform search')
      }

      const data = await response.json()
      
      // Transform API response to match our interface
      const searchResults: SearchResult[] = data.results.map((result: any, index: number) => ({
        id: result.url || Date.now().toString() + index,
        title: result.name || `Search Result ${index + 1}`,
        url: result.url || '#',
        snippet: result.snippet || 'No description available',
        hostName: result.host_name || 'unknown.com',
        timestamp: new Date(),
        rank: index + 1
      }))
      
      setSearchResults(searchResults)
    } catch (error) {
      console.error('Error performing search:', error)
      toast({
        title: "Search Error",
        description: "Failed to perform web search. Showing fallback results.",
        variant: "destructive",
      })
      // Show error message or fallback to mock results
      const mockResults: SearchResult[] = [
        {
          id: Date.now().toString(),
          title: `Search results for: ${query}`,
          url: 'https://example.com/search-result',
          snippet: `Failed to perform web search. This is a fallback result for "${query}".`,
          hostName: 'example.com',
          timestamp: new Date(),
          rank: 1
        }
      ]
      setSearchResults(mockResults)
    } finally {
      setIsSearching(false)
    }
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Web Search</h1>
          <p className="text-muted-foreground">
            AI-powered web search and information retrieval
          </p>
        </div>
        <Badge variant="outline">
          <Search className="mr-2 h-4 w-4" />
          {searchResults.length} results
        </Badge>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Search Panel */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Search</CardTitle>
              <CardDescription>
                Enter your search query
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search the web..."
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !isSearching) {
                      handleSearch()
                    }
                  }}
                  disabled={isSearching}
                />
                <Button
                  onClick={handleSearch}
                  disabled={!query.trim() || isSearching}
                  size="sm"
                >
                  {isSearching ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Search className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="mt-4">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Trending Searches
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {trendingSearches.map((trend, index) => (
                <Button
                  key={index}
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start text-left h-auto p-2"
                  onClick={() => {
                    setQuery(trend)
                    handleSearch()
                  }}
                >
                  <span className="text-sm">{trend}</span>
                </Button>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Search Results */}
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <CardTitle>Search Results</CardTitle>
              <CardDescription>
                {query ? `Results for "${query}"` : 'Enter a search query to see results'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {searchResults.length === 0 ? (
                <div className="text-center py-12">
                  <Globe className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">No search results</h3>
                  <p className="text-muted-foreground">
                    Enter a search query to find information on the web
                  </p>
                </div>
              ) : (
                <ScrollArea className="max-h-[600px]">
                  <div className="space-y-4">
                    {searchResults.map((result) => (
                      <Card key={result.id} className="hover:shadow-md transition-shadow">
                        <CardContent className="p-4">
                          <div className="space-y-2">
                            <div className="flex items-start justify-between gap-2">
                              <h3 className="font-medium text-blue-600 hover:text-blue-800 cursor-pointer">
                                {result.title}
                              </h3>
                              <Badge variant="outline" className="text-xs">
                                #{result.rank}
                              </Badge>
                            </div>
                            
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <Globe className="h-3 w-3" />
                              <span className="truncate">{result.hostName}</span>
                              <Clock className="h-3 w-3 ml-auto" />
                              <span>{formatTime(result.timestamp)}</span>
                            </div>
                            
                            <p className="text-sm text-muted-foreground line-clamp-2">
                              {result.snippet}
                            </p>
                            
                            <div className="flex items-center gap-2">
                              <Button variant="outline" size="sm" className="text-xs">
                                <ExternalLink className="mr-1 h-3 w-3" />
                                Visit
                              </Button>
                              <Button variant="outline" size="sm" className="text-xs">
                                <Copy className="mr-1 h-3 w-3" />
                                Copy
                              </Button>
                              <Button variant="outline" size="sm" className="text-xs">
                                <Star className="mr-1 h-3 w-3" />
                                Save
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}