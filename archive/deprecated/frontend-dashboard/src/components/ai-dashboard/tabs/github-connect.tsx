'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui'
import { Button } from '@acme/ui'
import { Input } from '@acme/ui'
import { Badge } from '@acme/ui'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@acme/ui'
import { 
  Github, 
  ExternalLink, 
  GitBranch, 
  GitCommit, 
  GitPullRequest,
  GitMerge,
  Star,
  Users,
  Activity,
  Code,
  FileText,
  Settings,
  CheckCircle,
  AlertCircle,
  Clock,
  Zap
} from 'lucide-react'

interface Repository {
  id: string
  name: string
  description: string
  language: string
  stars: number
  forks: number
  lastUpdated: Date
  status: 'connected' | 'disconnected' | 'error'
}

interface ActivityItem {
  id: string
  type: 'commit' | 'pull_request' | 'issue' | 'star'
  repository: string
  title: string
  author: string
  timestamp: Date
  status: 'success' | 'pending' | 'error'
}

export function GithubConnect() {
  const [repositories, setRepositories] = useState<Repository[]>([
    {
      id: '1',
      name: 'catcatAI/Unified-AI-Project',
      description: 'Advanced multi-dimensional semantic AI system',
      language: 'Python',
      stars: 142,
      forks: 28,
      lastUpdated: new Date(Date.now() - 3600000),
      status: 'connected'
    },
    {
      id: '2',
      name: 'catcatAI/github-connect-quest',
      description: 'GitHub integration and automation tools',
      language: 'TypeScript',
      stars: 67,
      forks: 12,
      lastUpdated: new Date(Date.now() - 7200000),
      status: 'connected'
    },
    {
      id: '3',
      name: 'catcatAI/ai-dashboard',
      description: 'Modern AI dashboard with Next.js',
      language: 'TypeScript',
      stars: 89,
      forks: 15,
      lastUpdated: new Date(Date.now() - 1800000),
      status: 'disconnected'
    }
  ])

  const [recentActivity, setRecentActivity] = useState<ActivityItem[]>([
    {
      id: '1',
      type: 'commit',
      repository: 'Unified-AI-Project',
      title: 'feat: Add neural network monitoring dashboard',
      author: 'AI Assistant',
      timestamp: new Date(Date.now() - 300000),
      status: 'success'
    },
    {
      id: '2',
      type: 'pull_request',
      repository: 'github-connect-quest',
      title: 'Enhance GitHub API integration',
      author: 'Dev Bot',
      timestamp: new Date(Date.now() - 600000),
      status: 'pending'
    },
    {
      id: '3',
      type: 'issue',
      repository: 'ai-dashboard',
      title: 'Bug: Mobile responsive layout issues',
      author: 'User Report',
      timestamp: new Date(Date.now() - 900000),
      status: 'error'
    },
    {
      id: '4',
      type: 'star',
      repository: 'Unified-AI-Project',
      title: 'Repository starred by user',
      author: 'Community',
      timestamp: new Date(Date.now() - 1200000),
      status: 'success'
    }
  ])

  const [githubToken, setGithubToken] = useState('')
  const [isConnecting, setIsConnecting] = useState(false)

  const handleConnectGitHub = async () => {
    if (!githubToken.trim()) return

    setIsConnecting(true)

    // Simulate GitHub connection
    setTimeout(() => {
      setIsConnecting(false)
      // Update repository statuses
      setRepositories(prev => prev.map(repo => ({
        ...repo,
        status: 'connected'
      })))
    }, 2000)
  }

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'commit':
        return <GitCommit className="h-4 w-4" />
      case 'pull_request':
        return <GitPullRequest className="h-4 w-4" />
      case 'issue':
        return <AlertCircle className="h-4 w-4" />
      case 'star':
        return <Star className="h-4 w-4" />
      default:
        return <Activity className="h-4 w-4" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
      case 'success':
        return 'text-green-600'
      case 'disconnected':
        return 'text-gray-600'
      case 'pending':
        return 'text-yellow-600'
      case 'error':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
      case 'success':
        return <CheckCircle className="h-4 w-4" />
      case 'disconnected':
        return <Clock className="h-4 w-4" />
      case 'pending':
        return <Clock className="h-4 w-4 animate-spin" />
      case 'error':
        return <AlertCircle className="h-4 w-4" />
      default:
        return <Clock className="h-4 w-4" />
    }
  }

  const formatTime = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    
    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes}m ago`
    if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`
    return `${Math.floor(minutes / 1440)}d ago`
  }

  const totalStars = repositories.reduce((sum, repo) => sum + repo.stars, 0)
  const totalForks = repositories.reduce((sum, repo) => sum + repo.forks, 0)
  const connectedRepos = repositories.filter(repo => repo.status === 'connected').length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">GitHub Connect</h1>
          <p className="text-muted-foreground">
            Connect and manage your GitHub repositories with AI-powered automation
          </p>
        </div>
        <Badge variant="outline">
          <Github className="mr-2 h-4 w-4" />
          {connectedRepos} connected
        </Badge>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Repositories</CardTitle>
            <Github className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{repositories.length}</div>
            <p className="text-xs text-muted-foreground">
              {connectedRepos} connected
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Stars</CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalStars}</div>
            <p className="text-xs text-muted-foreground">
              Across all repos
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Forks</CardTitle>
            <GitBranch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalForks}</div>
            <p className="text-xs text-muted-foreground">
              Community contributions
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Activity</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{recentActivity.length}</div>
            <p className="text-xs text-muted-foreground">
              Recent events
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="repositories" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="repositories">Repositories</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
          <TabsTrigger value="automation">Automation</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="repositories" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Connected Repositories</CardTitle>
              <CardDescription>
                Manage your GitHub repository connections
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {repositories.map((repo) => (
                  <Card key={repo.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="font-medium">{repo.name}</h3>
                            <Badge variant="outline">{repo.language}</Badge>
                            <div className={`flex items-center gap-1 ${getStatusColor(repo.status)}`}>
                              {getStatusIcon(repo.status)}
                              <span className="text-xs capitalize">{repo.status}</span>
                            </div>
                          </div>
                          <p className="text-sm text-muted-foreground mb-2">
                            {repo.description}
                          </p>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Star className="h-3 w-3" />
                              {repo.stars}
                            </div>
                            <div className="flex items-center gap-1">
                              <GitBranch className="h-3 w-3" />
                              {repo.forks}
                            </div>
                            <div>Updated {formatTime(repo.lastUpdated)}</div>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm">
                            <ExternalLink className="mr-1 h-3 w-3" />
                            View
                          </Button>
                          <Button variant="outline" size="sm">
                            <Settings className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>
                Latest GitHub events across connected repositories
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentActivity.map((activity) => (
                  <div key={activity.id} className="flex items-center gap-3 p-3 rounded-lg border">
                    <div className={`p-2 rounded-full ${
                      activity.status === 'success' ? 'bg-green-100' :
                      activity.status === 'pending' ? 'bg-yellow-100' :
                      'bg-red-100'
                    }`}>
                      {getActivityIcon(activity.type)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium">{activity.title}</span>
                        <Badge variant="outline" className="text-xs">
                          {activity.repository}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span>by {activity.author}</span>
                        <span>•</span>
                        <span>{formatTime(activity.timestamp)}</span>
                      </div>
                    </div>
                    <div className={`flex items-center gap-1 ${getStatusColor(activity.status)}`}>
                      {getStatusIcon(activity.status)}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="automation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>AI-Powered Automation</CardTitle>
              <CardDescription>
                Configure AI automation for your repositories
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <Card className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Code className="h-5 w-5" />
                    <h3 className="font-medium">Code Review</h3>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">
                    AI-powered code review and suggestions
                  </p>
                  <Button variant="outline" size="sm" className="w-full">
                    Configure
                  </Button>
                </Card>
                
                <Card className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <GitCommit className="h-5 w-5" />
                    <h3 className="font-medium">Commit Analysis</h3>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">
                    Analyze commit messages and changes
                  </p>
                  <Button variant="outline" size="sm" className="w-full">
                    Configure
                  </Button>
                </Card>
                
                <Card className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <GitPullRequest className="h-5 w-5" />
                    <h3 className="font-medium">PR Automation</h3>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">
                    Automated PR reviews and merging
                  </p>
                  <Button variant="outline" size="sm" className="w-full">
                    Configure
                  </Button>
                </Card>
                
                <Card className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <FileText className="h-5 w-5" />
                    <h3 className="font-medium">Documentation</h3>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">
                    Auto-generate documentation
                  </p>
                  <Button variant="outline" size="sm" className="w-full">
                    Configure
                  </Button>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>GitHub Settings</CardTitle>
              <CardDescription>
                Configure your GitHub integration settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">GitHub Personal Access Token</label>
                <Input
                  type="password"
                  value={githubToken}
                  onChange={(e) => setGithubToken(e.target.value)}
                  placeholder="ghp_..."
                />
                <p className="text-xs text-muted-foreground">
                  Required for accessing GitHub API. Generate one from GitHub Settings &gt; Developer settings.
                </p>
              </div>
              
              <Button
                onClick={handleConnectGitHub}
                disabled={!githubToken.trim() || isConnecting}
                className="w-full"
              >
                {isConnecting ? (
                  <>
                    <Clock className="mr-2 h-4 w-4 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <Github className="mr-2 h-4 w-4" />
                    Connect to GitHub
                  </>
                )}
              </Button>
              
              <div className="pt-4 border-t">
                <h4 className="font-medium mb-2">Connected Services</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">GitHub API</span>
                    <Badge variant="outline">Connected</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Webhooks</span>
                    <Badge variant="outline">Active</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">AI Automation</span>
                    <Badge variant="outline">Enabled</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}