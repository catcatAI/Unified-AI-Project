'use client'

import { useState } from 'react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { 
  Users, 
  MessageSquare, 
  FileText,
  Calendar,
  Video,
  Share,
  Plus,
  Search,
  Activity,
  CheckCircle
} from 'lucide-react'

interface TeamMember {
  id: string
  name: string
  role: string
  status: 'online' | 'offline' | 'busy'
  last_seen: string
}

interface ChatMessage {
  id: string
  user: string
  message: string
  timestamp: string
}

interface Workspace {
  id: string
  name: string
  members: number
  last_activity: string
}

const mockMembers: TeamMember[] = [
  {
    id: '1',
    name: '張三',
    role: '項目經理',
    status: 'online',
    last_seen: '剛剛'
  },
  {
    id: '2',
    name: '李四',
    role: '開發工程師',
    status: 'busy',
    last_seen: '5 分鐘前'
  },
  {
    id: '3',
    name: '王五',
    role: '設計師',
    status: 'online',
    last_seen: '剛剛'
  },
  {
    id: '4',
    name: '趙六',
    role: '測試工程師',
    status: 'offline',
    last_seen: '1 小時前'
  }
]

const mockMessages: ChatMessage[] = [
  {
    id: '1',
    user: '張三',
    message: '大家好，今天的會議準時開始嗎？',
    timestamp: '10:30'
  },
  {
    id: '2',
    user: '李四',
    message: '是的，我已經準備好了',
    timestamp: '10:32'
  },
  {
    id: '3',
    user: '王五',
    message: '我也準備好了，可以開始',
    timestamp: '10:33'
  }
]

const mockWorkspaces: Workspace[] = [
  {
    id: '1',
    name: 'AI 統一平台開發',
    members: 8,
    last_activity: '2 分鐘前'
  },
  {
    id: '2',
    name: '前端界面設計',
    members: 4,
    last_activity: '15 分鐘前'
  },
  {
    id: '3',
    name: '後端API開發',
    members: 6,
    last_activity: '1 小時前'
  }
]

export function UnifiedTeamCollaboration() {
  const [members] = useState<TeamMember[]>(mockMembers)
  const [messages] = useState<ChatMessage[]>(mockMessages)
  const [workspaces] = useState<Workspace[]>(mockWorkspaces)
  const [newMessage, setNewMessage] = useState('')

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'text-green-600 bg-green-50'
      case 'busy': return 'text-yellow-600 bg-yellow-50'
      case 'offline': return 'text-gray-600 bg-gray-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return <CheckCircle className="h-3 w-3 text-green-500" />
      case 'busy': return <Activity className="h-3 w-3 text-yellow-500" />
      case 'offline': return <Activity className="h-3 w-3 text-gray-500" />
      default: return <Activity className="h-3 w-3 text-gray-500" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'online': return '在線'
      case 'busy': return '忙碌'
      case 'offline': return '離線'
      default: return '未知'
    }
  }

  const handleSendMessage = () => {
    if (!newMessage.trim()) return
    // 實現發送消息邏輯
    setNewMessage('')
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">團隊協作</h1>
          <p className="text-muted-foreground">
            實時團隊通信與工作空間管理
          </p>
        </div>
        
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          創建工作空間
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Team Members */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                團隊成員 ({members.length})
              </CardTitle>
              <CardDescription>
                當前在線成員狀態
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {members.map((member) => (
                <div key={member.id} className="flex items-center justify-between p-3 border rounded">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                      <span className="text-sm font-medium">
                        {member.name.charAt(0)}
                      </span>
                    </div>
                    <div>
                      <div className="font-medium text-sm">{member.name}</div>
                      <div className="text-xs text-muted-foreground">{member.role}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(member.status)}
                    <Badge variant="outline" className={getStatusColor(member.status)}>
                      {getStatusText(member.status)}
                    </Badge>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Workspaces */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Share className="h-5 w-5" />
                工作空間
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {workspaces.map((workspace) => (
                <div key={workspace.id} className="p-3 border rounded">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-sm">{workspace.name}</h4>
                    <Badge variant="outline">{workspace.members} 成員</Badge>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    最後活動: {workspace.last_activity}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Team Chat */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="h-[600px] flex flex-col">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                團隊聊天
              </CardTitle>
              <CardDescription>
                與團隊成員實時交流
              </CardDescription>
            </CardHeader>
            
            <CardContent className="flex-1 flex flex-col p-0">
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.map((message) => (
                  <div key={message.id} className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <span className="text-sm font-medium">
                        {message.user.charAt(0)}
                      </span>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-sm">{message.user}</span>
                        <span className="text-xs text-muted-foreground">{message.timestamp}</span>
                      </div>
                      <div className="text-sm bg-muted rounded-lg px-3 py-2">
                        {message.message}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Message Input */}
              <div className="border-t p-4">
                <div className="flex gap-2">
                  <Input
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="輸入消息..."
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  />
                  <Button onClick={handleSendMessage}>
                    發送
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardContent className="p-4 text-center">
                <Video className="h-8 w-8 mx-auto mb-2 text-blue-500" />
                <div className="text-sm font-medium">視頻會議</div>
                <div className="text-xs text-muted-foreground">啟動會議</div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 text-center">
                <Calendar className="h-8 w-8 mx-auto mb-2 text-green-500" />
                <div className="text-sm font-medium">日程安排</div>
                <div className="text-xs text-muted-foreground">查看日曆</div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 text-center">
                <FileText className="h-8 w-8 mx-auto mb-2 text-purple-500" />
                <div className="text-sm font-medium">共享文檔</div>
                <div className="text-xs text-muted-foreground">文檔協作</div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}