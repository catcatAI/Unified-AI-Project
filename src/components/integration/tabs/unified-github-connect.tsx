'use client'

import { useState } from 'react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  Github, 
  GitBranch, 
  GitPullRequest,
  GitCommit,
  Star,
  Users,
  Activity,
  ExternalLink,
  Settings,
  RefreshCw
} from 'lucide-react'

interface Repository {
  id: string
  name: string
  description: string
  language: string
  stars: number
  forks: number
  last_updated: string
  is_private: boolean
}

interface Activity {
  type: 'push' | 'pull_request' | 'issue' | 'star'
  repo: string
  action: string
  time: string
  user: string
}

const mockRepos: Repository[] = [
  {
    id: '1',
    name: 'unified-ai-project',
    description: '統一AI平台核心項目',
    language: 'Python',
    stars: 234,
    forks: 45,
    last_updated: '2 小時前',
    is_private: false
  },
  {
    id: '2',
    name: 'ai-dashboard',
    description: 'AI統一儀表板界面',
    language: 'TypeScript',
    stars: 189,
    forks: 32,
    last_updated: '1 天前',
    is_private: false
  },
  {
    id: '3',
    name: 'github-connect-quest',
    description: 'GitHub自動化工具',
    language: 'JavaScript',
    stars: 156,
    forks: 28,
    last_updated: '3 天前',
    is_private: false
  }
]

const mockActivities: Activity[] = [
  {
    type: 'push',
    repo: 'unified-ai-project',
    action: '推送了 3 個提交到 main 分支',
    time: '2 小時前',
    user: 'developer1'
  },
  {
    type: 'pull_request',
    repo: 'ai-dashboard',
    action: '創建了新的 Pull Request',
    time: '5 小時前',
    user: 'developer2'
  },
  {
    type: 'issue',
    repo: 'github-connect-quest',
    action: '關閉了一個 Issue',
    time: '1 天前',
    user: 'developer3'
  },
  {
    type: 'star',
    repo: 'unified-ai-project',
    action: '給項目點了星',
    time: '2 天前',
    user: 'user1'
  }
]

export function UnifiedGithubConnect() {
  const [repositories] = useState<Repository[]>(mockRepos)
  const [activities] = useState<Activity[]>(mockActivities)
  const [isConnected, setIsConnected] = useState(true)

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'push': return <GitCommit className="h-4 w-4 text-green-500" />
      case 'pull_request': return <GitPullRequest className="h-4 w-4 text-blue-500" />
      case 'issue': return <GitBranch className="h-4 w-4 text-orange-500" />
      case 'star': return <Star className="h-4 w-4 text-yellow-500" />
      default: return <Activity className="h-4 w-4 text-gray-500" />
    }
  }

  const getLanguageColor = (language: string) => {
    const colors: Record<string, string> = {
      'Python': 'text-blue-600 bg-blue-50',
      'TypeScript': 'text-blue-700 bg-blue-100',
      'JavaScript': 'text-yellow-600 bg-yellow-50',
      'Java': 'text-red-600 bg-red-50',
      'C++': 'text-purple-600 bg-purple-50'
    }
    return colors[language] || 'text-gray-600 bg-gray-50'
  }

  const getTotalStats = () => {
    const totalStars = repositories.reduce((sum, repo) => sum + repo.stars, 0)
    const totalForks = repositories.reduce((sum, repo) => sum + repo.forks, 0)
    const publicRepos = repositories.filter(repo => !repo.is_private).length

    return {
      totalStars,
      totalForks,
      publicRepos,
      totalRepos: repositories.length
    }
  }

  const stats = getTotalStats()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">GitHub 連接</h1>
          <p className="text-muted-foreground">
            GitHub倉庫管理與自動化
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Badge variant={isConnected ? 'default' : 'secondary'}>
            {isConnected ? '已連接' : '未連接'}
          </Badge>
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4 mr-1" />
            設置
          </Button>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">倉庫總數</CardTitle>
            <Github className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalRepos}</div>
            <p className="text-xs text-muted-foreground">
              已連接倉庫
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">總星標數</CardTitle>
            <Star className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalStars}</div>
            <p className="text-xs text-muted-foreground">
              獲得的星標
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">分支數</CardTitle>
            <GitBranch className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalForks}</div>
            <p className="text-xs text-muted-foreground">
              分支總數
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">公開倉庫</CardTitle>
            <Users className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.publicRepos}</div>
            <p className="text-xs text-muted-foreground">
              公開可見
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Repositories */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Github className="h-5 w-5" />
                  倉庫列表
                </CardTitle>
                <Button variant="outline" size="sm">
                  <RefreshCw className="h-4 w-4 mr-1" />
                  刷新
                </Button>
              </div>
              <CardDescription>
                已連接的GitHub倉庫
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {repositories.map((repo) => (
                  <div key={repo.id} className="p-4 border rounded-lg">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-medium">{repo.name}</h3>
                          {repo.is_private && (
                            <Badge variant="secondary" className="text-xs">
                              私有
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">
                          {repo.description}
                        </p>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <span className={`px-2 py-1 rounded ${getLanguageColor(repo.language)}`}>
                              {repo.language}
                            </span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Star className="h-3 w-3" />
                            <span>{repo.stars}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <GitBranch className="h-3 w-3" />
                            <span>{repo.forks}</span>
                          </div>
                          <span>更新於 {repo.last_updated}</span>
                        </div>
                      </div>
                      <Button variant="outline" size="sm">
                        <ExternalLink className="h-3 w-3 mr-1" />
                        查看
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                最近活動
              </CardTitle>
              <CardDescription>
                GitHub上的最新活動
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {activities.map((activity, index) => (
                  <div key={index} className="flex items-start gap-3 p-3 border rounded">
                    {getActivityIcon(activity.type)}
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate">
                        {activity.repo}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {activity.action}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {activity.user} • {activity.time}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">快速操作</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full justify-start">
                <GitCommit className="h-4 w-4 mr-2" />
                創建提交
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <GitPullRequest className="h-4 w-4 mr-2" />
                創建 Pull Request
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <GitBranch className="h-4 w-4 mr-2" />
                創建分支
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <ExternalLink className="h-4 w-4 mr-2" />
                打開 GitHub
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}