'use client'

import { useState, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Search, 
  ExternalLink, 
  Loader2,
  Clock,
  Globe,
  Star,
  Copy,
  AlertCircle,
  CheckCircle
} from 'lucide-react'

interface SearchResult {
  url: string
  name: string
  snippet: string
  host_name: string
  rank: number
  date: string
  favicon: string
}

interface SearchHistory {
  id: string
  query: string
  timestamp: Date
  resultsCount: number
}

export function UnifiedWebSearch() {
  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searchHistory, setSearchHistory] = useState<SearchHistory[]>([])
  const [resultCount, setResultCount] = useState(10)

  const searchInputRef = useRef<HTMLInputElement>(null)

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
        setSearchResults(data.results || [])
        
        // 添加到搜索歷史
        const newHistory: SearchHistory = {
          id: Date.now().toString(),
          query,
          timestamp: new Date(),
          resultsCount: data.results?.length || 0
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

  const popularSearches = [
    '人工智能最新發展',
    'React 18 新特性',
    'TypeScript 最佳實踐',
    'Next.js 教程',
    '機器學習入門'
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">網路搜索</h1>
          <p className="text-muted-foreground">
            AI驅動的智能搜索服務
          </p>
        </div>
        
        <Badge variant="outline">
          結果數量: {resultCount}
        </Badge>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Search Panel */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                搜索
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
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">結果數量</label>
                <div className="flex gap-2">
                  {[5, 10, 20].map((count) => (
                    <Button
                      key={count}
                      variant={resultCount === count ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setResultCount(count)}
                      disabled={isSearching}
                    >
                      {count}
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
                    搜索
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Popular Searches */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">熱門搜索</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {popularSearches.map((search, index) => (
                <div
                  key={index}
                  className="p-2 rounded border cursor-pointer hover:border-primary/50 transition-colors"
                  onClick={() => {
                    setQuery(search)
                    setTimeout(() => handleSearch(), 100)
                  }}
                >
                  <div className="text-sm flex items-center gap-2">
                    <Star className="h-3 w-3 text-yellow-500" />
                    {search}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Search History */}
          {searchHistory.length > 0 && (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-lg">搜索歷史</CardTitle>
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
          {isSearching && (
            <Card>
              <CardContent className="flex items-center justify-center h-32">
                <div className="text-center">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
                  <p className="text-muted-foreground">正在搜索...</p>
                </div>
              </CardContent>
            </Card>
          )}

          {!isSearching && searchResults.length === 0 && query && (
            <Card>
              <CardContent className="flex items-center justify-center h-32">
                <div className="text-center">
                  <AlertCircle className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
                  <p className="text-muted-foreground">未找到相關結果</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    請嘗試使用不同的關鍵詞
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {!isSearching && !query && (
            <Card>
              <CardContent className="flex items-center justify-center h-32">
                <div className="text-center">
                  <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">
                    輸入關鍵詞開始搜索
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {searchResults.map((result, index) => (
            <Card key={`${result.url}-${index}`}>
              <CardContent className="p-4">
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <img
                      src={getFaviconUrl(result.url)}
                      alt=""
                      className="w-4 h-4 mt-1 flex-shrink-0"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none'
                      }}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <h3 className="font-medium text-sm truncate">{result.name}</h3>
                        <Badge variant="outline" className="text-xs flex-shrink-0">
                          #{result.rank}
                        </Badge>
                      </div>
                      
                      <div className="text-xs text-muted-foreground mb-2">
                        <div className="flex items-center gap-2">
                          <span className="truncate">{result.host_name}</span>
                          <span>•</span>
                          <span>{formatDate(result.date)}</span>
                        </div>
                      </div>
                      
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {result.snippet}
                      </p>
                      
                      <div className="flex items-center justify-between mt-3">
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
                          複製鏈接
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}