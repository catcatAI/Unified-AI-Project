import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  MessageSquare, 
  Activity, 
  BookOpen, 
  Gamepad2,
  Brain,
  Network,
  Zap,
  Code,
  Settings
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: '儀表板' },
  { to: '/chat', icon: MessageSquare, label: 'AI 對話' },
  { to: '/monitor', icon: Activity, label: '系統監控' },
  { to: '/docs', icon: BookOpen, label: '文檔' },
  { to: '/game', icon: Gamepad2, label: "Angela's World" },
  { to: '/architecture-editor', icon: Network, label: '架構編輯器' },
  { to: '/function-editor', icon: Zap, label: '功能編輯器' },
  { to: '/code-editor', icon: Code, label: '代碼編輯器' },
  { to: '/atlassian', icon: Settings, label: 'Atlassian 管理' },
];

export function Sidebar() {
  return (
    <div className="w-64 bg-card border-r border-border flex flex-col">
      <div className="p-6">
        <div className="flex items-center gap-2">
          <Brain className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-lg font-bold text-foreground">Unified AI</h1>
            <p className="text-sm text-muted-foreground">Project Control</p>
          </div>
        </div>
      </div>
      
      <nav className="flex-1 px-4">
        <ul className="space-y-2">
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors",
                    "hover:bg-accent hover:text-accent-foreground",
                    isActive 
                      ? "bg-primary text-primary-foreground" 
                      : "text-muted-foreground"
                  )
                }
              >
                <item.icon className="h-5 w-5" />
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      
      <div className="p-4 border-t border-border">
        <div className="text-xs text-muted-foreground">
          版本 0.1.0
        </div>
      </div>
    </div>
  );
}