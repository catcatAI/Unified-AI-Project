'use client'

import React, { useState, useRef, useEffect } from 'react'
import { useChat, useChatArchive } from '@/hooks/use-api-data'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui'
import { Button } from '@acme/ui'
import { Input } from '@acme/ui'
import { ScrollArea } from '@acme/ui'
import { Badge } from '@acme/ui'
import { Textarea } from '@acme/ui'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@acme/ui'
import { useToast } from '@/hooks/use-toast'
import { 
  Send, 
  MessageSquare, 
  Bot, 
  User, 
  Clock,
  ThumbsUp,
  ThumbsDown,
  Copy,
  Archive,
  Mic,
  MicOff,
  Paperclip,
  MoreHorizontal,
  Settings,
  Trash2,
  Edit,
  Share,
  Volume2,
  VolumeX,
  Sparkles,
  Zap,
  Brain
} from 'lucide-react'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  model?: string
  rating?: 'positive' | 'negative' | null
}

export function EnhancedAIChat() {
  const { toast } = useToast()
  const { messages, loading: isLoading, error, sendMessage } = useChat()
  const { saveChatToArchive } = useChatArchive()
  const [inputValue, setInputValue] = useState('')
  const [selectedModel, setSelectedModel] = useState('gpt-4')
  const [isRecording, setIsRecording] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [voiceEnabled, setVoiceEnabled] = useState(false)
  const [temperature, setTemperature] = useState(0.7)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollElement = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (scrollElement) {
        scrollElement.scrollTop = scrollElement.scrollHeight
      }
    }
  }, [messages, isLoading])

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    try {
      // Send message and get response
      await sendMessage(inputValue)
      
      // Save to archive
      const lastAssistantMessage = messages[messages.length - 1]
      if (lastAssistantMessage && lastAssistantMessage.type === 'assistant') {
        await saveChatToArchive(inputValue, lastAssistantMessage.content)
      }
      
      setInputValue('')
      
      toast({
        title: "Message sent",
        description: "AI response received successfully",
      })
    } catch (err) {
      console.error('Error sending message:', err)
      toast({
        title: "Error",
        description: error || "Failed to send message. Please try again.",
        variant: "destructive",
      })
    }
  }

  const handleRateMessage = (messageId: string, rating: 'positive' | 'negative') => {
    // In a real implementation, this would update the message rating
    toast({
      title: "Feedback recorded",
      description: `Message ${rating === 'positive' ? 'liked' : 'disliked'}`,
    })
  }

  const handleCopyMessage = (content: string) => {
    navigator.clipboard.writeText(content)
    toast({
      title: "Copied to clipboard",
      description: "Message content copied successfully",
    })
  }

  const handleArchiveMessage = (userMessage: string, aiMessage: string) => {
    saveChatToArchive(userMessage, aiMessage)
    toast({
      title: "Saved to archive",
      description: "Conversation saved successfully",
    })
  }

  const formatTime = (date: Date) => {
    if (!(date instanceof Date) || isNaN(date.getTime())) {
      return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Enhanced AI Chat</h1>
          <p className="text-muted-foreground">
            Advanced conversational AI interface with enhanced features
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">
            <MessageSquare className="mr-2 h-4 w-4" />
            {messages.length} messages
          </Badge>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setShowSettings(!showSettings)}
          >
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-4 flex-1">
        {/* Chat Area */}
        <div className="lg:col-span-3 flex flex-col">
          <Card className="flex-1 flex flex-col">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Conversation</CardTitle>
                <CardDescription>
                  Chat with AI assistant
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Select value={selectedModel} onValueChange={setSelectedModel}>
                  <SelectTrigger className="w-32">
                    <SelectValue placeholder="Model" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gpt-4">
                      <div className="flex items-center gap-2">
                        <Sparkles className="h-4 w-4" />
                        GPT-4
                      </div>
                    </SelectItem>
                    <SelectItem value="claude">
                      <div className="flex items-center gap-2">
                        <Brain className="h-4 w-4" />
                        Claude
                      </div>
                    </SelectItem>
                    <SelectItem value="llama">
                      <div className="flex items-center gap-2">
                        <Zap className="h-4 w-4" />
                        Llama 2
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setVoiceEnabled(!voiceEnabled)}
                >
                  {voiceEnabled ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              <ScrollArea className="flex-1 pr-4" ref={scrollAreaRef}>
                <div className="space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex gap-3 ${
                        message.type === 'user' ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      {message.type === 'assistant' && (
                        <div className="flex-shrink-0 mt-1">
                          <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                            <Bot className="h-4 w-4 text-primary" />
                          </div>
                        </div>
                      )}
                      <div className="max-w-[85%]">
                        <div
                          className={`rounded-lg p-3 ${
                            message.type === 'user'
                              ? 'bg-primary text-primary-foreground'
                              : 'bg-muted'
                          }`}
                        >
                          <div className="text-sm whitespace-pre-wrap">
                            {message.content}
                          </div>
                        </div>
                        <div className="flex items-center justify-between mt-2 px-1">
                          <div className="flex items-center gap-2 text-xs opacity-70">
                            <Clock className="h-3 w-3" />
                            {formatTime(message.timestamp)}
                            {message.model && (
                              <Badge variant="secondary" className="text-xs">
                                {message.model}
                              </Badge>
                            )}
                          </div>
                          {message.type === 'assistant' && (
                            <div className="flex gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0"
                                onClick={() => handleRateMessage(message.id, 'positive')}
                              >
                                <ThumbsUp 
                                  className={`h-3 w-3 ${
                                    message.rating === 'positive' ? 'text-green-500' : ''
                                  }`} 
                                />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0"
                                onClick={() => handleRateMessage(message.id, 'negative')}
                              >
                                <ThumbsDown 
                                  className={`h-3 w-3 ${
                                    message.rating === 'negative' ? 'text-red-500' : ''
                                  }`} 
                                />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0"
                                onClick={() => handleCopyMessage(message.content)}
                              >
                                <Copy className="h-3 w-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0"
                                onClick={() => {
                                  // Find the corresponding user message
                                  const userMessage = messages.find(
                                    (m, i) => 
                                      m.type === 'user' && 
                                      i < messages.findIndex(msg => msg.id === message.id)
                                  )
                                  if (userMessage) {
                                    handleArchiveMessage(userMessage.content, message.content)
                                  }
                                }}
                              >
                                <Archive className="h-3 w-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0"
                              >
                                <MoreHorizontal className="h-3 w-3" />
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>
                      {message.type === 'user' && (
                        <div className="flex-shrink-0 mt-1">
                          <div className="w-8 h-8 bg-secondary rounded-full flex items-center justify-center">
                            <User className="h-4 w-4" />
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                  {isLoading && (
                    <div className="flex gap-3 justify-start">
                      <div className="flex-shrink-0 mt-1">
                        <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                          <Bot className="h-4 w-4 text-primary" />
                        </div>
                      </div>
                      <div className="bg-muted rounded-lg p-3">
                        <div className="flex gap-1">
                          <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                          <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>
              
              {/* Input Area */}
              <div className="mt-4 space-y-3">
                {showSettings && (
                  <Card className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium">Chat Settings</h4>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => setShowSettings(false)}
                      >
                        Close
                      </Button>
                    </div>
                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium">Temperature: {temperature}</label>
                        <input 
                          type="range" 
                          min="0" 
                          max="1" 
                          step="0.1" 
                          value={temperature}
                          onChange={(e) => setTemperature(parseFloat(e.target.value))}
                          className="w-full"
                        />
                        <p className="text-xs text-muted-foreground mt-1">
                          Controls randomness: Lower for focused, higher for creative
                        </p>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Voice Responses</span>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => setVoiceEnabled(!voiceEnabled)}
                        >
                          {voiceEnabled ? 'Enabled' : 'Disabled'}
                        </Button>
                      </div>
                    </div>
                  </Card>
                )}
                
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="icon"
                    onClick={() => setIsRecording(!isRecording)}
                    className={isRecording ? 'animate-pulse bg-red-500 text-white' : ''}
                  >
                    {isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                  </Button>
                  <Button variant="outline" size="icon">
                    <Paperclip className="h-4 w-4" />
                  </Button>
                  <Textarea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="Type your message..."
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey && !isLoading) {
                        e.preventDefault()
                        handleSendMessage()
                      }
                    }}
                    disabled={isLoading}
                    rows={1}
                    className="min-h-10 max-h-32 resize-none"
                  />
                  <Button
                    onClick={handleSendMessage}
                    disabled={isLoading || !inputValue.trim()}
                    size="icon"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Sidebar */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Conversation History</CardTitle>
              <CardDescription>
                Recent chats
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {[1, 2, 3, 4, 5].map((item) => (
                <div 
                  key={item}
                  className="p-2 rounded-lg hover:bg-muted cursor-pointer text-sm"
                >
                  <div className="font-medium">Conversation {item}</div>
                  <div className="text-xs text-muted-foreground truncate">
                    This is a sample conversation summary...
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Quick Prompts</CardTitle>
              <CardDescription>
                Common requests
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {[
                "Explain quantum computing",
                "Write a poem about AI",
                "Debug this code",
                "Summarize recent news"
              ].map((prompt, index) => (
                <Button
                  key={index}
                  variant="outline"
                  className="w-full h-auto py-2 text-left text-sm justify-start"
                  onClick={() => setInputValue(prompt)}
                >
                  {prompt}
                </Button>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}