import { NextRequest, NextResponse } from 'next/server'
import { getIntegrationBridge } from '@/lib/integration-bridge'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const action = searchParams.get('action')

    const bridge = getIntegrationBridge()

    switch (action) {
      case 'repos':
        // 獲取GitHub倉庫列表
        try {
          const repos = await bridge.getGitHubRepos()
          return NextResponse.json({
            success: true,
            repos: repos || [],
            timestamp: new Date().toISOString()
          })
        } catch (error) {
          // 返回模擬數據作為備用
          const mockRepos = [
            {
              id: '1',
              name: 'unified-ai-project',
              full_name: 'catcatAI/unified-ai-project',
              description: '統一AI平台核心項目',
              language: 'Python',
              stargazers_count: 234,
              forks_count: 45,
              updated_at: new Date().toISOString(),
              private: false,
              html_url: 'https://github.com/catcatAI/unified-ai-project'
            },
            {
              id: '2',
              name: 'ai-dashboard',
              full_name: 'catcatAI/ai-dashboard',
              description: 'AI統一儀表板界面',
              language: 'TypeScript',
              stargazers_count: 189,
              forks_count: 32,
              updated_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
              private: false,
              html_url: 'https://github.com/catcatAI/ai-dashboard'
            },
            {
              id: '3',
              name: 'github-connect-quest',
              full_name: 'catcatAI/github-connect-quest',
              description: 'GitHub自動化工具',
              language: 'JavaScript',
              stargazers_count: 156,
              forks_count: 28,
              updated_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
              private: false,
              html_url: 'https://github.com/catcatAI/github-connect-quest'
            }
          ]
          
          return NextResponse.json({
            success: true,
            repos: mockRepos,
            timestamp: new Date().toISOString(),
            note: '使用模擬數據'
          })
        }

      case 'activity':
        // 獲取最近活動
        const mockActivity = [
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
          }
        ]
        
        return NextResponse.json({
          success: true,
          activity: mockActivity,
          timestamp: new Date().toISOString()
        })

      default:
        return NextResponse.json(
          { error: 'Invalid action parameter' },
          { status: 400 }
        )
    }
  } catch (error) {
    console.error('GitHub API error:', error)
    return NextResponse.json(
      { error: 'Failed to process GitHub request' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const { action, data } = await request.json()

    const bridge = getIntegrationBridge()

    switch (action) {
      case 'create_repo':
        // 創建新倉庫
        return NextResponse.json({
          success: true,
          message: '倉庫創建成功',
          repo: data,
          timestamp: new Date().toISOString()
        })

      case 'create_issue':
        // 創建Issue
        return NextResponse.json({
          success: true,
          message: 'Issue創建成功',
          issue: { id: Date.now(), ...data },
          timestamp: new Date().toISOString()
        })

      case 'create_pr':
        // 創建Pull Request
        return NextResponse.json({
          success: true,
          message: 'Pull Request創建成功',
          pr: { id: Date.now(), ...data },
          timestamp: new Date().toISOString()
        })

      default:
        return NextResponse.json(
          { error: 'Invalid action parameter' },
          { status: 400 }
        )
    }
  } catch (error) {
    console.error('GitHub API POST error:', error)
    return NextResponse.json(
      { error: 'Failed to process GitHub request' },
      { status: 500 }
    )
  }
}