import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from '@/components/theme-provider';
import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { Dashboard } from '@/pages/dashboard';
import { AIChat } from '@/pages/ai-chat';
import { SystemMonitor } from '@/pages/system-monitor';
import { Documentation } from '@/pages/documentation';
import { AngelaGame } from '@/pages/angela-game';
import ArchitectureEditor from '@/pages/architecture-editor';
import FunctionEditor from '@/pages/function-editor';
import CodeEditor from '@/pages/code-editor';
import { AtlassianManagement } from '@/pages/atlassian-management';

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <ThemeProvider defaultTheme="dark" storageKey="unified-ai-theme">
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <div className="flex h-screen bg-background">
            <Sidebar />
            <div className="flex-1 flex flex-col overflow-hidden">
              <Header />
              <main className="flex-1 overflow-auto p-6">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/chat" element={<AIChat />} />
                  <Route path="/monitor" element={<SystemMonitor />} />
                  <Route path="/docs" element={<Documentation />} />
                  <Route path="/game" element={<AngelaGame />} />
                  <Route path="/architecture-editor" element={<ArchitectureEditor />} />
                  <Route path="/function-editor" element={<FunctionEditor />} />
                  <Route path="/code-editor" element={<CodeEditor />} />
                  <Route path="/atlassian" element={<AtlassianManagement />} />
                  <Route path="*" element={<Dashboard />} />
                </Routes>
              </main>
            </div>
          </div>
        </BrowserRouter>
      </ThemeProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
