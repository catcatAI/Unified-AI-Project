import { Bell, LogOut, User, Code2, Sparkles } from "lucide-react"
import { Button } from "./ui/button"
import { ThemeToggle } from "./ui/theme-toggle"
import { useAuth } from "@/contexts/AuthContext"
import { useNavigate } from "react-router-dom"
import { Avatar, AvatarFallback } from "./ui/avatar"

export function Header() {
  const { logout } = useAuth()
  const navigate = useNavigate()
  
  const handleLogout = () => {
    console.log("User logging out")
    logout()
    navigate("/login")
  }
  
  return (
    <header className="fixed top-0 z-50 w-full border-b border-slate-200/50 dark:border-slate-700/50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-lg">
      <div className="flex h-16 items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-600 rounded-lg flex items-center justify-center">
              <Code2 className="w-4 h-4 text-white" />
            </div>
            <div className="flex flex-col">
              <div className="text-lg font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent">
                Unified AI Project
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1">
                <Sparkles className="w-3 h-3" />
                CodeInspect Integration
              </div>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="h-5 w-5" />
            <span className="absolute -top-1 -right-1 h-3 w-3 bg-gradient-to-r from-red-500 to-pink-500 rounded-full animate-pulse"></span>
          </Button>
          
          <ThemeToggle />
          
          <div className="flex items-center gap-3">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-600 text-white text-sm">
                <User className="h-4 w-4" />
              </AvatarFallback>
            </Avatar>
            
            <Button variant="ghost" size="icon" onClick={handleLogout} className="hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20">
              <LogOut className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  )
}