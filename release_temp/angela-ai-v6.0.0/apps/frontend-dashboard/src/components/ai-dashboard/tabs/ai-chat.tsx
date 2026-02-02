'use client'

import React, { useState } from 'react'
import { useChat, useChatArchive } from '@/hooks/use-api-data'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@acme/ui'
import { Button } from '@acme/ui'
import { Input } from '@acme/ui'
import { ScrollArea } from '@acme/ui'
import { Badge } from '@acme/ui'
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
  Archive
} from 'lucide-react'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  model?: string
}

export function AIChat() {
  const { toast } = useToast()
  const { messages, loading: isLoading, error, sendMessage } = useChat()
  const { saveChatToArchive } = useChatArchive()
  const [inputValue, setInputValue] = useState('')

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

  const formatTime = (date: Date) => {
    if (!(date instanceof Date) || isNaN(date.getTime())) {
      return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Chat</h1>
          <p className="text-muted-foreground">
            Conversational AI interface for natural language interactions
          </p>
        </div>
        <Badge variant="outline">
          <MessageSquare className="mr-2 h-4 w-4" />
          {messages.length} messages
        </Badge>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Chat History */}
        <div className="lg:col-span-3">
          <Card className="h-[600px] flex flex-col">
            <CardHeader>
              <CardTitle>Conversation</CardTitle>
              <CardDescription>
                Chat with AI assistant
              </CardDescription>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              <ScrollArea className="flex-1 pr-4">
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
                          <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                            <Bot className="h-4 w-4 text-primary" />
                          </div>
                        </div>
                      )}
                      <div
                        className={`max-w-[80%] rounded-lg p-3 ${
                          message.type === 'user'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted'
                        }`}
                      >
                        <div className="text-sm whitespace-pre-wrap">
                          {message.content}
                        </div>
                        <div className="flex items-center justify-between mt-2">
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
                              >
                                <ThumbsUp className="h-3 w-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0"
                              >
                                <ThumbsDown className="h-3 w-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0"
                              >
                                <Copy className="h-3 w-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0"
                                onClick={() => {
                                  // Save this message to archive
                                  saveChatToArchive(
                                    messages.find(m => m.type === 'user' && m.id < message.id)?.content || '',
                                    message.content
                                  )
                                  toast({
                                    title: "Saved",
                                    description: "Message saved to archive",
                                  })
                                }}
                              >
                                <Archive className="h-3 w-3" />
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>
                      {message.type === 'user' && (
                        <div className="flex-shrink-0">
                          <div className="w-8 h-8 bg-secondary rounded-full flex items-center justify-center">
                            <User className="h-4 w-4" />
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                  {isLoading && (
                    <div className="flex gap-3 justify-start">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                          <Bot className="h-4 w-4 text-primary" />
                        </div>
                      </div>
                      <div className="bg-muted rounded-lg p-3">
                        <div className="text-sm">Thinking...</div>
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>
              <div className="flex gap-2 mt-4">
                <Input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Type your message..."
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !isLoading) {
                      handleSendMessage()
                    }
                  }}
                  disabled={isLoading}
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={isLoading || !inputValue.trim()}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}