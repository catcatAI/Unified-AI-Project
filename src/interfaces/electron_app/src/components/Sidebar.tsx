import { useNavigate, useLocation } from "react-router-dom"
import {
  MessageSquare,
  Image,
  Mic,
  BarChart3,
  Code,
  Wrench,
  Home,
  History,
  Workflow,
  Settings,
  Sparkles,
  Languages,
  Eye,
  Volume2,
  Database,
  Gamepad2,
  Network
} from "lucide-react"
import {
  Sidebar as SidebarComponent,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
} from "./ui/sidebar"
import { Badge } from "./ui/badge"

const navigationItems = [
  {
    title: "Dashboard",
    url: "/",
    icon: Home,
  },
  {
    title: "Chat",
    url: "/chat",
    icon: MessageSquare,
  },
  {
    title: "HSP Network",
    url: "/hsp",
    icon: Network,
  },
  {
    title: "Game",
    url: "/game",
    icon: Gamepad2,
  },
  {
    title: "Code Inspector",
    url: "/code-analysis",
    icon: Code,
  },
  {
    title: "History",
    url: "/history",
    icon: History,
  },
  {
    title: "Workflows",
    url: "/workflows",
    icon: Workflow,
  },
  {
    title: "Settings",
    url: "/settings",
    icon: Settings,
  },
]

const aiCategories = [
  {
    title: "Text & Language",
    icon: MessageSquare,
    services: [
      { name: "GPT-4", id: "gpt-4", status: "active" },
      { name: "Claude", id: "claude", status: "active" },
      { name: "Translation", id: "translation", status: "active" },
      { name: "Summarization", id: "summarization", status: "active" },
    ]
  },
  {
    title: "Image & Vision",
    icon: Image,
    services: [
      { name: "DALL-E 3", id: "dalle-3", status: "active" },
      { name: "Stable Diffusion", id: "stable-diffusion", status: "active" },
      { name: "Image Analysis", id: "image-analysis", status: "active" },
      { name: "Image Editing", id: "image-editing", status: "maintenance" },
    ]
  },
  {
    title: "Audio & Speech",
    icon: Mic,
    services: [
      { name: "Whisper", id: "whisper", status: "active" },
      { name: "Text-to-Speech", id: "tts", status: "active" },
      { name: "Voice Clone", id: "voice-clone", status: "beta" },
    ]
  },
  {
    title: "Data & Analytics",
    icon: BarChart3,
    services: [
      { name: "Data Processing", id: "data-processing", status: "active" },
      { name: "Chart Generation", id: "chart-generation", status: "active" },
      { name: "Insights", id: "insights", status: "active" },
    ]
  },
  {
    title: "Code & Development",
    icon: Code,
    services: [
      { name: "Code Generation", id: "code-generation", status: "active" },
      { name: "Code Review", id: "code-review", status: "active" },
      { name: "Debugging", id: "debugging", status: "active" },
    ]
  },
]

export function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500'
      case 'maintenance': return 'bg-yellow-500'
      case 'beta': return 'bg-blue-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <SidebarComponent className="border-r bg-background/50 backdrop-blur-sm">
      <SidebarHeader className="p-4">
        <div className="flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-blue-600" />
          <span className="font-semibold">AI Services</span>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navigationItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    onClick={() => navigate(item.url)}
                    isActive={location.pathname === item.url}
                    className="hover:bg-accent/50 transition-colors"
                  >
                    <item.icon className="h-4 w-4" />
                    <span>{item.title}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {aiCategories.map((category) => (
          <SidebarGroup key={category.title}>
            <SidebarGroupLabel className="flex items-center gap-2">
              <category.icon className="h-4 w-4" />
              {category.title}
            </SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {category.services.map((service) => (
                  <SidebarMenuItem key={service.id}>
                    <SidebarMenuButton
                      onClick={() => navigate(`/service/${service.id}`)}
                      isActive={location.pathname === `/service/${service.id}`}
                      className="hover:bg-accent/50 transition-colors"
                    >
                      <div className={`h-2 w-2 rounded-full ${getStatusColor(service.status)}`} />
                      <span className="flex-1">{service.name}</span>
                      {service.status === 'beta' && (
                        <Badge variant="secondary" className="text-xs">Beta</Badge>
                      )}
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>

      <SidebarFooter className="p-4">
        <div className="text-xs text-muted-foreground">
          <div>API Usage: 1,234 / 10,000</div>
          <div className="w-full bg-secondary rounded-full h-1 mt-1">
            <div className="bg-blue-600 h-1 rounded-full" style={{ width: '12.34%' }} />
          </div>
        </div>
      </SidebarFooter>
    </SidebarComponent>
  )
}
