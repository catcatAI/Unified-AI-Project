import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Bot, User, Brain, MessageSquare } from 'lucide-react';

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  agent?: string;
}

export function AIChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'ai',
      content: '您好！我是統一AI系統的DialogueManager。我可以協助您處理各種任務，包括數據分析、創意寫作、邏輯推理等。請告訴我您需要什麼幫助？',
      timestamp: new Date(),
      agent: 'DialogueManager'
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: `我收到了您的訊息："${inputValue}"。這是一個模擬回應。在實際部署中，這裡會連接到真正的DialogueManager和代理系統來處理您的請求。`,
        timestamp: new Date(),
        agent: 'Angela Meta-Agent'
      };
      setMessages(prev => [...prev, aiMessage]);
      setIsLoading(false);
    }, 1500);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="h-full flex flex-col space-y-4">
      <div>
        <h1 className="text-3xl font-bold text-foreground">AI 對話系統</h1>
        <p className="text-muted-foreground">與統一AI系統的DialogueManager交互</p>
      </div>

      <div className="flex-1 flex gap-4">
        {/* Chat Area */}
        <Card className="flex-1 flex flex-col">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              對話會話
            </CardTitle>
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
                    <div
                      className={`flex gap-3 max-w-[80%] ${
                        message.type === 'user' ? 'flex-row-reverse' : 'flex-row'
                      }`}
                    >
                      <div className="flex-shrink-0">
                        {message.type === 'user' ? (
                          <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                            <User className="h-4 w-4 text-primary-foreground" />
                          </div>
                        ) : (
                          <div className="w-8 h-8 bg-secondary rounded-full flex items-center justify-center">
                            <Bot className="h-4 w-4 text-secondary-foreground" />
                          </div>
                        )}
                      </div>
                      <div className={`space-y-1 ${message.type === 'user' ? 'text-right' : 'text-left'}`}>
                        <div
                          className={`p-3 rounded-lg ${
                            message.type === 'user'
                              ? 'bg-primary text-primary-foreground ml-4'
                              : 'bg-muted text-muted-foreground mr-4'
                          }`}
                        >
                          {message.content}
                        </div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <span>{message.timestamp.toLocaleTimeString()}</span>
                          {message.agent && (
                            <Badge variant="outline" className="text-xs">
                              {message.agent}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex gap-3">
                    <div className="w-8 h-8 bg-secondary rounded-full flex items-center justify-center">
                      <Bot className="h-4 w-4 text-secondary-foreground" />
                    </div>
                    <div className="bg-muted p-3 rounded-lg mr-4">
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
            
            <div className="flex gap-2 mt-4">
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="輸入您的訊息..."
                disabled={isLoading}
                className="flex-1"
              />
              <Button 
                onClick={handleSendMessage} 
                disabled={isLoading || !inputValue.trim()}
                size="icon"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Agent Info Panel */}
        <Card className="w-80">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              活躍代理
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { name: 'Angela Meta-Agent', status: '協調中', specialty: '任務分解與協調' },
                { name: 'Data Analyst Agent', status: '待機', specialty: '數據分析與處理' },
                { name: 'Creative Writer Agent', status: '待機', specialty: '創意寫作' },
                { name: 'Logic Reasoner Agent', status: '待機', specialty: '邏輯推理' },
              ].map((agent) => (
                <div key={agent.name} className="p-3 border border-border rounded-lg">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-sm">{agent.name}</span>
                    <Badge 
                      variant={agent.status === '協調中' ? 'default' : 'secondary'}
                      className="text-xs"
                    >
                      {agent.status}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">{agent.specialty}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}