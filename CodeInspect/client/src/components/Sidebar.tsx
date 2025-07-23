import { NavLink } from "react-router-dom"
import { Code2, History, Settings, FileText, Zap, Brain } from "lucide-react"
import { cn } from "@/lib/utils"

const navigation = [
  { name: 'Code Analysis', href: '/code-analysis', icon: Code2, description: 'AI-powered code inspection' },
  { name: 'Project History', href: '/project-history', icon: History, description: 'View past analyses' },
  { name: 'Settings', href: '/settings', icon: Settings, description: 'Configure preferences' },
]

export function Sidebar() {
  return (
    <div className="fixed left-0 top-16 h-[calc(100vh-4rem)] w-64 bg-white/80 dark:bg-slate-900/80 backdrop-blur-lg border-r border-slate-200/50 dark:border-slate-700/50">
      <div className="flex flex-col h-full p-4">
        <div className="flex items-center gap-2 mb-8 px-2">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-600 rounded-lg flex items-center justify-center">
            <Brain className="w-4 h-4 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-slate-900 dark:text-slate-100 text-sm">CodeInspect</span>
            <span className="text-xs text-slate-500 dark:text-slate-400">AI Code Analysis</span>
          </div>
        </div>

        <nav className="flex-1">
          <ul className="space-y-2">
            {navigation.map((item) => (
              <li key={item.name}>
                <NavLink
                  to={item.href}
                  className={({ isActive }) =>
                    cn(
                      "flex flex-col gap-1 px-3 py-3 rounded-lg text-sm font-medium transition-all duration-200 group",
                      isActive
                        ? "bg-gradient-to-r from-blue-500 via-purple-500 to-indigo-600 text-white shadow-lg shadow-blue-500/25"
                        : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100"
                    )
                  }
                >
                  <div className="flex items-center gap-3">
                    <item.icon className="w-5 h-5" />
                    {item.name}
                  </div>
                  <span className="text-xs opacity-75 ml-8">
                    {item.description}
                  </span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="mt-auto p-3 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg border border-blue-200/50 dark:border-blue-800/50">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <span className="text-sm font-medium text-blue-900 dark:text-blue-100">AI Powered</span>
          </div>
          <p className="text-xs text-blue-700 dark:text-blue-300">
            Advanced code analysis with machine learning insights
          </p>
        </div>
      </div>
    </div>
  )
}