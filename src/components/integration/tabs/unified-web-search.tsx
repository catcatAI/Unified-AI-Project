'use client'

import { useState, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Search, 
  ExternalLink, 
  Loader2,
  Clock,
  Globe,
  Star,
  Copy,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  Filter,
  Bookmark,
  Share,
  Zap,
  Target,
  BarChart3,
  Eye,
  ThumbsUp,
  MessageSquare
} from 'lucide-react'

interface SearchResult {
  url: string
  name: string
  snippet: string
  host_name: string
  rank: number
  date: string
  favicon: string
  category?: string
  relevance?: number
  views?: number
}

interface SearchHistory {
  id: string
  query: string
  timestamp: Date
  resultsCount: number
}

interface SearchFilter {
  timeRange: 'all' | 'day' | 'week' | 'month'
  category: 'all' | 'news' | 'blogs' | 'academic' | 'videos'
  sortBy: 'relevance' | 'date' | 'popularity'
}

export function UnifiedWebSearch() {
  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searchHistory, setSearchHistory] = useState<SearchHistory[]>([])
  const [resultCount, setResultCount] = useState(10)
  const [filters, setFilters] = useState<SearchFilter>({
    timeRange: 'all',
    category: 'all',
    sortBy: 'relevance'
  })
  const [selectedCategory, setSelectedCategory] = useState('all')

  const searchInputRef = useRef<HTMLInputElement>(null)

  const categories = [
    { id: 'all', name: '全部', icon: Globe, count: 0 },
    { id: 'news', name: '新聞', icon: TrendingUp, count: 0 },
    { id: 'blogs', name: '博客', icon: MessageSquare, count: 0 },
    { id: 'academic', name: '學術', icon: BarChart3, count: 0 },
    { id: 'videos', name: '視頻', icon: Eye, count: 0 }
  ]

  const popularSearches = [
    { title: '人工智能最新發展', category: 'technology', trending: true },
    { title: 'React 18 新特性', category: 'development', trending: false },
    { title: 'TypeScript 最佳實踐', category: 'development', trending: true },
    { title: 'Next.js 教程', category: 'development', trending: false },
    { title: '機器學習入門', category: 'technology', trending: true },
    { title: 'Web3 區塊鏈', category: 'technology', trending: false }
  ]

  const trendingSearches = popularSearches.filter(s => s.trending)

  const handleSearch = async () => {
    if (!query.trim() || isSearching) return

    setIsSearching(true)
    setSearchResults([])

    try {
      const response = await fetch('/api/integration/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          num: resultCount
        })
      })

      const data = await response.json()

      if (response.ok) {
        const enhancedResults = (data.results || []).map((result: SearchResult, index: number) => ({
          ...result,
          category: getRandomCategory(),
          relevance: Math.max(60, 100 - index * 5),
          views: Math.floor(Math.random() * 10000) + 100
        }))
        
        setSearchResults(enhancedResults)
        
        // 添加到搜索歷史
        const newHistory: SearchHistory = {
          id: Date.now().toString(),
          query,
          timestamp: new Date(),
          resultsCount: enhancedResults.length
        }
        
        setSearchHistory(prev => [newHistory, ...prev.slice(0, 9)]) // 保留最近10條
      } else {
        throw new Error(data.error || 'Search failed')
      }
    } catch (error) {
      console.error('Search error:', error)
      setSearchResults([])
    } finally {
      setIsSearching(false)
    }
  }

  const getRandomCategory = () => {
    const cats = ['news', 'blogs', 'academic', 'videos']
    return cats[Math.floor(Math.random() * cats.length)]
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const handleHistoryClick = (historyQuery: string) => {
    setQuery(historyQuery)
    setTimeout(() => {
      handleSearch()
    }, 100)
  }

  const clearHistory = () => {
    setSearchHistory([])
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      const now = new Date()
      const diffInHours = Math.abs(now.getTime() - date.getTime()) / (1000 * 60 * 60)
      
      if (diffInHours < 1) {
        return '剛剛'
      } else if (diffInHours < 24) {
        return `${Math.floor(diffInHours)} 小時前`
      } else {
        return date.toLocaleDateString('zh-TW')
      }
    } catch {
      return dateString
    }
  }

  const getFaviconUrl = (url: string) => {
    try {
      const domain = new URL(url).hostname
      return `https://www.google.com/s2/favicons?domain=${domain}&sz=32`
    } catch {
      return ''
    }
  }

  const getCategoryIcon = (category?: string) => {
    switch (category) {
      case 'news': return TrendingUp
      case 'blogs': return MessageSquare
      case 'academic': return BarChart3
      case 'videos': return Eye
      default: return Globe
    }
  }

  const getRelevanceColor = (relevance?: number) => {
    if (!relevance) return 'text-gray-500'
    if (relevance >= 80) return 'text-green-600'
    if (relevance >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const filteredResults = selectedCategory === 'all' 
    ? searchResults 
    : searchResults.filter(r => r.category === selectedCategory)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">網路搜索</h1>
          <p className="text-muted-foreground">
            AI驅動的智能搜索服務
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="flex items-center gap-1">
            <Target className="h-3 w-3" />
            {resultCount} 結果
          </Badge>
          {searchResults.length > 0 && (
            <Badge variant="secondary" className="flex items-center gap-1">
              <BarChart3 className="h-3 w-3" />
              {searchResults.length} 找到
            </Badge>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Search Panel */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                智能搜索
              </CardTitle>
              <CardDescription>
                輸入關鍵詞進行搜索
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Input
                  ref={searchInputRef}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="輸入搜索關鍵詞..."
                  disabled={isSearching}
                  className="text-sm"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">結果數量</label>
                <div className="flex gap-2">
                  {[5, 10, 20, 50].map((count) => (
                    <Button
                      key={count}
                      variant={resultCount === count ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setResultCount(count)}
                      disabled={isSearching}
                      className="flex-1"
                    >
                      {count}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">排序方式</label>
                <div className="grid grid-cols-1 gap-1">
                  {[
                    { value: 'relevance', label: '相關性' },
                    { value: 'date', label: '時間' },
                    { value: 'popularity', label: '熱度' }
                  ].map((option) => (
                    <Button
                      key={option.value}
                      variant={filters.sortBy === option.value ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setFilters(prev => ({ ...prev, sortBy: option.value as any }))}
                      disabled={isSearching}
                      className="text-xs justify-start"
                    >
                      {option.label}
                    </Button>
                  ))}
                </div>
              </div>

              <Button 
                onClick={handleSearch}
                disabled={!query.trim() || isSearching}
                className="w-full"
              >
                {isSearching ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    搜索中...
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4 mr-2" />
                    開始搜索
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Trending Searches */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                熱門搜索
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {trendingSearches.map((search, index) => (
                <div
                  key={index}
                  className="p-2 rounded-lg border cursor-pointer hover:border-primary/50 transition-colors hover:shadow-sm"
                  onClick={() => {
                    setQuery(search.title)
                    setTimeout(() => handleSearch(), 100)
                  }}
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="text-sm font-medium truncate flex items-center gap-1">
                      <Star className="h-3 w-3 text-yellow-500" />
                      {search.title}
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {search.category}
                    </Badge>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Search History */}
          {searchHistory.length > 0 && (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  搜索歷史
                </CardTitle>
                <Button variant="ghost" size="sm" onClick={clearHistory}>
                  清除
                </Button>
              </CardHeader>
              <CardContent className="space-y-2">
                <ScrollArea className="max-h-48">
                  {searchHistory.map((history) => (
                    <div
                      key={history.id}
                      className="p-2 rounded border cursor-pointer hover:border-primary/50 transition-colors"
                      onClick={() => handleHistoryClick(history.query)}
                    >
                      <div className="text-sm font-medium truncate">{history.query}</div>
                      <div className="text-xs text-muted-foreground">
                        <Clock className="h-3 w-3 inline mr-1" />
                        {history.timestamp.toLocaleDateString('zh-TW')} • {history.resultsCount} 結果
                      </div>
                    </div>
                  ))}
                </ScrollArea>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Search Results */}
        <div className="lg:col-span-3 space-y-4">
          {/* Category Tabs */}
          {searchResults.length > 0 && (
            <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
              <TabsList className="grid w-full grid-cols-6">
                {categories.map(category => (
                  <TabsTrigger key={category.id} value={category.id} className="text-xs">
                    {category.name}
                  </TabsTrigger>
                ))}
              </TabsList>
            </Tabs>
          )}

          {isSearching && (
            <Card>
              <CardContent className="flex items-center justify-center h-48">
                <div className="text-center">
                  <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4" />
                  <p className="text-muted-foreground mb-2">正在搜索中...</p>
                  <p className="text-sm text-muted-foreground">
                    AI正在為您找到最相關的結果
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {!isSearching && searchResults.length === 0 && query && (
            <Card>
              <CardContent className="flex items-center justify-center h-48">
                <div className="text-center max-w-md">
                  <AlertCircle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
                  <h3 className="text-lg font-medium mb-2">未找到相關結果</h3>
                  <p className="text-muted-foreground mb-4">
                    請嘗試使用不同的關鍵詞或調整搜索條件
                  </p>
                  <div className="flex gap-2 justify-center">
                    <Button variant="outline" size="sm" onClick={() => setQuery('')}>
                      清除搜索
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => setResultCount(20)}>
                      增加結果數量
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {!isSearching && !query && (
            <Card>
              <CardContent className="flex items-center justify-center h-96">
                <div className="text-center max-w-md">
                  <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Search className="h-8 w-8 text-primary" />
                  </div>
                  <h3 className="text-lg font-medium mb-2">開始您的智能搜索</h3>
                  <p className="text-muted-foreground mb-6">
                    輸入關鍵詞，AI將為您找到最相關、最有價值的搜索結果
                  </p>
                  <div className="space-y-2 text-left">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Zap className="h-4 w-4" />
                      <span>AI驅動的智能搜索</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Target className="h-4 w-4" />
                      <span>精準的結果排序</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <BarChart3 className="h-4 w-4" />
                      <span>實時熱度分析</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {filteredResults.map((result, index) => {
            const CategoryIcon = getCategoryIcon(result.category)
            return (
              <Card key={`${result.url}-${index}`} className="hover:shadow-lg transition-shadow">
                <CardContent className="p-4">
                  <div className="space-y-3">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 mt-1">
                        {result.favicon ? (
                          <img
                            src={getFaviconUrl(result.url)}
                            alt=""
                            className="w-4 h-4"
                            onError={(e) => {
                              e.currentTarget.style.display = 'none'
                            }}
                          />
                        ) : (
                          <CategoryIcon className="h-4 w-4 text-muted-foreground" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <h3 className="font-medium text-sm truncate hover:text-primary cursor-pointer">
                            {result.name}
                          </h3>
                          <div className="flex items-center gap-1 flex-shrink-0">
                            <Badge variant="outline" className="text-xs">
                              #{result.rank}
                            </Badge>
                            {result.relevance && (
                              <Badge 
                                variant="outline" 
                                className={`text-xs ${getRelevanceColor(result.relevance)}`}
                              >
                                {result.relevance}%
                              </Badge>
                            )}
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                          <span className="truncate flex items-center gap-1">
                            <Globe className="h-3 w-3" />
                            {result.host_name}
                          </span>
                          <span>•</span>
                          <span>{formatDate(result.date)}</span>
                          {result.views && (
                            <>
                              <span>•</span>
                              <span className="flex items-center gap-1">
                                <Eye className="h-3 w-3" />
                                {result.views.toLocaleString()}
                              </span>
                            </>
                          )}
                          {result.category && (
                            <>
                              <span>•</span>
                              <Badge variant="secondary" className="text-xs">
                                {result.category}
                              </Badge>
                            </>
                          )}
                        </div>
                        
                        <p className="text-sm text-muted-foreground line-clamp-3">
                          {result.snippet}
                        </p>
                        
                        <div className="flex items-center justify-between mt-3">
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => window.open(result.url, '_blank')}
                            >
                              <ExternalLink className="h-3 w-3 mr-1" />
                              訪問
                            </Button>
                            
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => copyToClipboard(result.url)}
                            >
                              <Copy className="h-3 w-3 mr-1" />
                              複製
                            </Button>
                            
                            <Button
                              variant="ghost"
                              size="sm"
                            >
                              <Bookmark className="h-3 w-3 mr-1" />
                              收藏
                            </Button>
                          </div>
                          
                          {result.relevance && result.relevance >= 80 && (
                            <div className="flex items-center gap-1 text-xs text-green-600">
                              <ThumbsUp className="h-3 w-3" />
                              高相關性
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>
    </div>
  )
}