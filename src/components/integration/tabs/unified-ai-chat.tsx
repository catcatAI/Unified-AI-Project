'use client'

import { useState, useRef, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Send, 
  Bot, 
  User, 
  Loader2,
  Copy,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  ThumbsUp,
  ThumbsDown,
  Share,
  Download,
  FileText,
  MessageSquare,
  Settings,
  Zap,
  Brain,
  Sparkles
} from 'lucide-react'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  service?: string
  model?: string
  status?: 'sending' | 'sent' | 'error'
  feedback?: 'like' | 'dislike' | null
}

interface ChatSession {
  id: string
  title: string
  createdAt: Date
  messageCount: number
  lastMessage: string
}

export function UnifiedAIChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: '您好！我是AI統一平台的智能助手。我可以幫助您進行對話、回答問題、提供資訊等。我有以下特色功能：\n\n🤖 **智能對話**：自然流暢的對話體驗\n🧠 **多模型支持**：可選擇不同的AI模型\n⚡ **快速響應**：實時回應您的問題\n📊 **對話歷史**：保存和管理對話記錄\n\n請隨時向我提問，我會盡力為您提供最佳的服務！',
      timestamp: new Date(),
      service: 'system',
      status: 'sent'
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [selectedModel, setSelectedModel] = useState('gpt-4')
  const [sessions, setSessions] = useState<ChatSession[]>([
    {
      id: '1',
      title: '歡迎對話',
      createdAt: new Date(),
      messageCount: 1,
      lastMessage: '您好！我是AI統一平台的智能助手...'
    }
  ])
  const [currentSessionId, setCurrentSessionId] = useState('1')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const models = [
    { id: 'gpt-4', name: 'GPT-4', description: '最強大的綜合模型', icon: Brain, color: 'text-blue-500' },
    { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', description: '快速響應模型', icon: Zap, color: 'text-green-500' },
    { id: 'claude', name: 'Claude', description: '對話優化模型', icon: MessageSquare, color: 'text-purple-500' },
    { id: 'gemini', name: 'Gemini', description: 'Google多模態模型', icon: Sparkles, color: 'text-orange-500' }
  ]

  const quickActions = [
    { title: '寫代碼', prompt: '請幫我寫一個Python函數來計算斐波那契數列' },
    { title: '翻譯文本', prompt: '請將以下英文翻譯成中文：Hello, how are you today?' },
    { title: '總結文章', prompt: '請幫我總結這篇文章的主要觀點...' },
    { title: '解釋概念', prompt: '請用簡單的語言解釋什麼是機器學習' }
  ]

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (messageText?: string) => {
    const textToSend = messageText || input
    if (!textToSend.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: textToSend,
      timestamp: new Date(),
      status: 'sent'
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setIsTyping(true)

    // 添加臨時的AI消息
    const aiMessage: Message = {
      id: (Date.now() + 1).toString(),
      type: 'assistant',
      content: '',
      timestamp: new Date(),
      status: 'sending'
    }

    setMessages(prev => [...prev, aiMessage])

    try {
      const response = await fetch('/api/integration/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: textToSend,
          model: selectedModel,
          userId: 'dashboard_user',
          sessionId: currentSessionId
        })
      })

      const data = await response.json()

      // 模擬打字效果
      setTimeout(() => {
        setIsTyping(false)
        
        if (response.ok) {
          // 更新AI消息
          setMessages(prev => prev.map(msg => 
            msg.id === aiMessage.id 
              ? {
                  ...msg,
                  content: data.response,
                  service: data.service,
                  model: data.model,
                  status: 'sent'
                }
              : msg
          ))
        } else {
          throw new Error(data.error || 'Failed to get response')
        }
      }, 1000)

    } catch (error) {
      console.error('Chat error:', error)
      setIsTyping(false)
      
      // 更新AI消息為錯誤狀態
      setMessages(prev => prev.map(msg => 
        msg.id === aiMessage.id 
          ? {
              ...msg,
              content: '抱歉，我現在無法回應您的問題。請稍後再試。',
              status: 'error'
            }
          : msg
      ))
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const handleFeedback = (messageId: string, feedback: 'like' | 'dislike') => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId 
        ? { ...msg, feedback: msg.feedback === feedback ? null : feedback }
        : msg
    ))
  }

  const clearChat = () => {
    setMessages([
      {
        id: '1',
        type: 'assistant',
        content: '聊天已清除。有什麼我可以幫助您的嗎？',
        timestamp: new Date(),
        service: 'system',
        status: 'sent'
      }
    ])
  }

  const exportChat = () => {
    const chatContent = messages.map(msg => 
      `${msg.type === 'user' ? '用戶' : 'AI'} [${formatTime(msg.timestamp)}]: ${msg.content}`
    ).join('\n\n')
    
    const blob = new Blob([chatContent], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `chat-${new Date().toISOString().split('T')[0]}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('zh-TW', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'sending':
        return <Loader2 className="h-3 w-3 animate-spin text-blue-500" />
      case 'sent':
        return <CheckCircle className="h-3 w-3 text-green-500" />
      case 'error':
        return <AlertCircle className="h-3 w-3 text-red-500" />
      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">AI 聊天</h1>
          <p className="text-muted-foreground">
            與統一AI助手進行智能對話
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="flex items-center gap-1">
            {models.find(m => m.id === selectedModel)?.icon && 
              React.createElement(models.find(m => m.id === selectedModel)!.icon, { 
                className: `h-3 w-3 ${models.find(m => m.id === selectedModel)?.color}` 
              })
            }
            {models.find(m => m.id === selectedModel)?.name}
          </Badge>
          <Button variant="outline" size="sm" onClick={exportChat}>
            <Download className="h-4 w-4 mr-1" />
            導出
          </Button>
          <Button variant="outline" size="sm" onClick={clearChat}>
            <RefreshCw className="h-4 w-4 mr-1" />
            清除
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Chat Interface */}
        <div className="lg:col-span-3 space-y-4">
          <Card className="h-[700px] flex flex-col">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5" />
                AI 對話
                {isTyping && (
                  <Badge variant="secondary" className="text-xs">
                    AI 正在輸入...
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                與AI助手進行實時對話
              </CardDescription>
            </CardHeader>
            
            <CardContent className="flex-1 flex flex-col p-0">
              <ScrollArea className="flex-1 px-4 py-3">
                <div className="space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex gap-3 ${
                        message.type === 'user' ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      {message.type === 'assistant' && (
                        <div className="flex-shrink-0">
                          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                            <Bot className="h-4 w-4 text-primary" />
                          </div>
                        </div>
                      )}
                      
                      <div className={`max-w-[80%] ${
                        message.type === 'user' ? 'order-1' : ''
                      }`}>
                        <div className={`rounded-lg px-3 py-2 ${
                          message.type === 'user'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted'
                        }`}>
                          <div className="whitespace-pre-wrap text-sm">
                            {message.content}
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                          <span>{formatTime(message.timestamp)}</span>
                          {message.service && (
                            <Badge variant="outline" className="text-xs">
                              {message.service}
                            </Badge>
                          )}
                          {getStatusIcon(message.status)}
                          
                          {message.type === 'assistant' && message.status === 'sent' && (
                            <>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-4 w-4 p-0"
                                onClick={() => copyToClipboard(message.content)}
                              >
                                <Copy className="h-3 w-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className={`h-4 w-4 p-0 ${message.feedback === 'like' ? 'text-green-500' : ''}`}
                                onClick={() => handleFeedback(message.id, 'like')}
                              >
                                <ThumbsUp className="h-3 w-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className={`h-4 w-4 p-0 ${message.feedback === 'dislike' ? 'text-red-500' : ''}`}
                                onClick={() => handleFeedback(message.id, 'dislike')}
                              >
                                <ThumbsDown className="h-3 w-3" />
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                      
                      {message.type === 'user' && (
                        <div className="flex-shrink-0">
                          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                            <User className="h-4 w-4 text-primary-foreground" />
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                  
                  {isLoading && (
                    <div className="flex gap-3">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                          <Bot className="h-4 w-4 text-primary" />
                        </div>
                      </div>
                      <div className="bg-muted rounded-lg px-3 py-2">
                        <div className="flex items-center gap-2">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span className="text-sm text-muted-foreground">
                            {isTyping ? 'AI 正在輸入...' : 'AI 正在思考...'}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>
              
              <div className="border-t p-4 space-y-3">
                {/* Quick Actions */}
                <div className="flex gap-2 flex-wrap">
                  {quickActions.map((action, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      size="sm"
                      onClick={() => handleSendMessage(action.prompt)}
                      className="text-xs"
                    >
                      {action.title}
                    </Button>
                  ))}
                </div>
                
                <div className="flex gap-2">
                  <Textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyPress}
                    placeholder="輸入您的問題... (按 Enter 發送，Shift+Enter 換行)"
                    className="flex-1 resize-none"
                    rows={2}
                    disabled={isLoading}
                  />
                  <Button 
                    onClick={() => handleSendMessage()}
                    disabled={!input.trim() || isLoading}
                    className="self-end"
                  >
                    {isLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <Tabs defaultValue="models" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="models" className="text-xs">模型</TabsTrigger>
              <TabsTrigger value="stats" className="text-xs">統計</TabsTrigger>
            </TabsList>
            
            <TabsContent value="models" className="space-y-3">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Settings className="h-4 w-4" />
                    模型選擇
                  </CardTitle>
                  <CardDescription>
                    選擇AI模型
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {models.map((model) => (
                    <div
                      key={model.id}
                      className={`p-3 rounded-lg border cursor-pointer transition-all hover:shadow-md ${
                        selectedModel === model.id
                          ? 'border-primary bg-primary/5 shadow-sm'
                          : 'border-border hover:border-primary/50'
                      }`}
                      onClick={() => setSelectedModel(model.id)}
                    >
                      <div className="flex items-center gap-2">
                        {React.createElement(model.icon, { 
                          className: `h-4 w-4 ${model.color}` 
                        })}
                        <div className="font-medium text-sm">{model.name}</div>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {model.description}
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </TabsContent>
            
            <TabsContent value="stats" className="space-y-3">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    統計信息
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">總消息數</span>
                    <span className="font-medium">{messages.length}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">用戶消息</span>
                    <span className="font-medium">
                      {messages.filter(m => m.type === 'user').length}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">AI回應</span>
                    <span className="font-medium">
                      {messages.filter(m => m.type === 'assistant').length}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">正面反饋</span>
                    <span className="font-medium text-green-600">
                      {messages.filter(m => m.feedback === 'like').length}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">負面反饋</span>
                    <span className="font-medium text-red-600">
                      {messages.filter(m => m.feedback === 'dislike').length}
                    </span>
                  </div>
                  <div className="pt-2 border-t">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">當前模型</span>
                      <Badge variant="outline" className="text-xs">
                        {models.find(m => m.id === selectedModel)?.name}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}