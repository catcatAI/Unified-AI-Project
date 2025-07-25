import React, { useState, useEffect, useRef } from 'react';
import { sendMessage, startSession } from '../api/chat';
import { useToast } from "@/components/ui/use-toast"

const Chat = () => {
  const { toast } = useToast()
  const [messages, setMessages] = useState<{ sender: string; text: string }[]>([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const chatDisplayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const initSession = async () => {
      try {
        const data = await startSession();
        setSessionId(data.session_id);
        setMessages([{ sender: 'ai', text: data.greeting }]);
      } catch (error) {
        toast({
          variant: "destructive",
          title: "Failed to start session",
          description: "Could not connect to the server. Please try again later.",
        })
      }
    };
    initSession();
  }, [toast]);

  useEffect(() => {
    if (chatDisplayRef.current) {
      chatDisplayRef.current.scrollTop = chatDisplayRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim() || !sessionId) return;

    const userMessage = { sender: 'user', text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    try {
      const data = await sendMessage(input, sessionId);
      const aiMessage = { sender: 'ai', text: data.response_text };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Failed to get response from AI",
        description: "Could not connect to the AI service. Please try again later.",
      })
    }
  };

  return (
    <div className="flex flex-col h-full">
      <h1 className="text-2xl font-bold mb-4">Chat</h1>
      <div ref={chatDisplayRef} className="flex-grow p-4 bg-gray-100 dark:bg-gray-800 rounded-lg overflow-y-auto">
        {messages.map((msg, index) => (
          <div key={index} className={`mb-2 p-2 rounded-md ${
            msg.sender === 'user' ? 'bg-blue-500 text-white self-end' :
            msg.sender === 'ai' ? 'bg-gray-300 dark:bg-gray-600' :
            'bg-red-500 text-white'
          }`}>
            <strong>{msg.sender === 'user' ? 'You' : msg.sender === 'ai' ? 'AI' : 'System'}: </strong>
            {msg.text}
          </div>
        ))}
      </div>
      <div className="mt-4 flex">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          className="flex-grow p-2 border rounded-l-md dark:bg-gray-700 dark:border-gray-600"
          placeholder="Type your message..."
        />
        <button
          onClick={handleSendMessage}
          className="px-4 py-2 bg-blue-500 text-white rounded-r-md hover:bg-blue-600"
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default Chat;
